#!/usr/bin/env python3
"""doc-impact search — find the docs a change touches.

Smarter-diff workflow, step 1: given a change summary (commands run, config
files touched, state changes observed), retrieve the runbook/reference pages
that talk about the same things — even when the wording differs — so the agent
can load them and correct any drift.

Index: reads the COMMITTED FTS5 index (scripts/docs/doc-impact/doc-index.db),
so clones get it for free and searches are ~10ms with no rebuild step. The
index is hash-synced by `doc-index.py sync` (run automatically via the
post-commit hook / after doc edits). If the index is missing or stale, this
script falls back to building a transient BM25 index in memory and hints at
running `doc-index.py sync`.

Retrieval is hybrid (the converged best practice in 2026 retrieval stacks:
lexical + fuzzy beats either alone at small-corpus scale):
  1. FTS5 bm25() ranking (porter-stemmed) over heading-aware doc chunks
  2. RapidFuzz partial-ratio boost for near-miss phrasing / renames
  3. Per-file dedupe so hits name a section, not just a file

Usage:
  uv run python scripts/docs/doc-impact/impact_search.py "swapped vg_k8s_fast for vg_k8s_nvme, recreated StorageClasses"
  uv run python scripts/docs/doc-impact/impact_search.py --json "disabled kube-proxy on rke2"   # machine-readable
  uv run python scripts/docs/doc-impact/impact_search.py --top 8 "..."                          # more candidates

Exit codes: 0 found candidates, 1 no index/corpus error.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "doc-index.db"
REPO = SCRIPT_DIR.parents[2]
DOC_ROOTS = [
    REPO / "docs" / "reference-design",
    REPO / "docs" / "implementation" / "_runbook",
    REPO / "docs" / "guides",
    REPO / "infra",  # infra docs/architecture.md etc.
]

# chunking: split markdown on headings; keep long sections under ~1200 chars
MAX_CHUNK = 1200


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in DOC_ROOTS:
        if root.exists():
            files.extend(root.rglob("*.md"))
    return sorted(files)


def chunk_markdown(path: Path) -> list[tuple[str, str, int]]:
    """Return [(chunk_id, text, line_no)] — heading-aware chunks."""
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    chunks: list[tuple[str, str, int]] = []
    buf: list[str] = []
    start_line = 1
    heading = ""

    def flush():
        nonlocal buf, start_line, heading
        if not buf:
            return
        body = "\n".join(buf).strip()
        if len(body) < 20:  # skip trivial fragments
            buf, start_line = [], 0
            return
        cid = f"{path}:{start_line}"
        prefix = f"{heading} — " if heading else ""
        chunks.append((cid, f"{path.name}: {prefix}{body}", start_line))
        buf, start_line = [], 0

    for i, line in enumerate(lines, start=1):
        if line.startswith("#"):
            flush()
            heading = line.lstrip("#").strip()
            start_line = i
            buf = [line]
        else:
            if not buf:
                start_line = i
            buf.append(line)
            if sum(len(x) for x in buf) > MAX_CHUNK:
                flush()
    flush()
    return chunks


def tokenize(text: str) -> list[str]:
    text = re.sub(r"`[^`]*`", " ", text)          # code spans: noise for BM25
    text = re.sub(r"[^a-zA-Z0-9_.\-/]+", " ", text.lower())
    stop = {
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is",
        "are", "be", "with", "as", "by", "that", "this", "it", "we", "use",
    }
    return [t for t in text.split() if t and t not in stop and len(t) > 1]


def _fts_query(query: str) -> str:
    """Build an OR-quoted FTS5 query from the raw text (safe: quoted prefix
    terms; punctuation dropped)."""
    words = [w for w in re.findall(r"[\w./-]+", query) if len(w) > 1]
    if not words:
        return ""
    # prefix match each token so 'stor' hits 'storageclasses'
    return " OR ".join(f'"{w}"*' for w in words[:24])


def search(query: str, top: int) -> list[dict]:
    from rapidfuzz import fuzz  # type: ignore

    q_low = query.lower()
    chunks: list[tuple[str, str, int, float]] = []  # (chunk_id, text, line, bm25)

    # --- primary path: committed FTS5 index --------------------------------
    if DB_PATH.exists():
        try:
            con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            fts = _fts_query(query)
            if fts:
                # chunk_id encodes "path::line"; join to recover line numbers
                rows = con.execute(
                    """
                    SELECT c.path, c.heading, c.body, h.chunk_id,
                           bm25(chunks) AS rank
                    FROM chunks c
                    JOIN chunk_hashes h ON h.chunk_id LIKE (c.path || '::%')
                    WHERE chunks MATCH ?
                    ORDER BY rank
                    LIMIT 400
                    """,
                    (fts,),
                ).fetchall()
                for row in rows:
                    line = int(row["chunk_id"].rsplit("::", 1)[1])
                    heading = row["heading"]
                    body = row["body"]
                    name = Path(row["path"]).name
                    text = f"{name}: {heading} — {body}" if heading else f"{name}: {body}"
                    # bm25() is negative-better; invert to a positive score
                    chunks.append((f"{row['path']}:{line}", text, line, -row["rank"]))
            con.close()
        except sqlite3.Error as e:
            print(f"note: committed index unusable ({e}); falling back",
                  file=sys.stderr)

    # --- fallback: transient BM25 index (index missing/stale/unusable) -----
    if not chunks:
        print("hint: run `python3 scripts/docs/doc-impact/doc-index.py sync` "
              "to refresh the committed index", file=sys.stderr)
        try:
            from rank_bm25 import BM25Okapi  # type: ignore
        except ImportError:
            sys.exit("rank-bm25 missing — cd projects && uv sync")
        files = []
        for root in DOC_ROOTS:
            if root.exists():
                files.extend(root.rglob("*.md"))
        files = sorted(files)
        for f in files:
            for cid, text, line in chunk_markdown(f):
                chunks.append((cid, text, line, 0.0))
        if not chunks:
            sys.exit("no markdown corpus found under docs/")
        bm25 = BM25Okapi([tokenize(c[1]) for c in chunks])
        q_tokens = tokenize(query)
        if q_tokens:
            scores = bm25.get_scores(q_tokens)
            chunks = [(cid, text, line, s)
                      for (cid, text, line, _), s in zip(chunks, scores)]

    results: list[dict] = []
    for cid, text, line, s in chunks:
        fz = fuzz.partial_ratio(q_low, text.lower()) / 100.0
        combined = float(s) + 2.5 * fz
        results.append(
            {"chunk": cid, "line": line, "bm25": round(float(s), 3),
             "fuzzy": round(fz, 3), "score": round(combined, 3), "text": text}
        )
    results.sort(key=lambda r: r["score"], reverse=True)


    # dedupe per file, keep best 2 chunks per file
    per_file: dict[str, int] = {}
    out: list[dict] = []
    for r in results:
        f = r["chunk"].rsplit(":", 1)[0]
        if per_file.get(f, 0) >= 2:
            continue
        per_file[f] = per_file.get(f, 0) + 1
        out.append(r)
        if len(out) >= top:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    _ = ap.add_argument("query", help="what changed (commands, configs, state)")
    _ = ap.add_argument("--top", type=int, default=6)
    _ = ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    results = search(args.query, args.top)
    if args.as_json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("no matching docs found")
        return
    print(f"docs to review for: {args.query!r}\n")
    for r in results:
        print(f"  {r['score']:>6.2f}  {r['chunk']}:{r['line']}")
        snippet = " ".join(r["text"].split())[:160]
        print(f"          {snippet}\n")
    print("Load each hit, compare its claims against the change, and update")
    print("anything stale before committing (see AGENTS.md Doc-impact rule).")


if __name__ == "__main__":
    main()