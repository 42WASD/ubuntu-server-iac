#!/usr/bin/env python3
"""doc-impact search — find the docs a change touches.

Smarter-diff workflow, step 1: given a change summary (commands run, config
files touched, state changes observed), retrieve the runbook/reference pages
that talk about the same things — even when the wording differs — so the agent
can load them and correct any drift.

Retrieval is hybrid (the converged best practice in 2026 retrieval stacks:
lexical + fuzzy beats either alone at small-corpus scale):
  1. BM25 lexical scoring (rank-bm25) over sentence-level doc chunks
  2. RapidFuzz partial-ratio boost for near-miss phrasing / renames
  3. Headings and chunk locality so hits name a section, not just a file

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
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
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


def build_index():
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except ImportError:
        sys.exit(
            "rank-bm25 missing — run: cd projects && uv add rank-bm25 rapidfuzz"
        )
    files = iter_markdown_files()
    chunks: list[tuple[str, str, int]] = []
    for f in files:
        chunks.extend(chunk_markdown(f))
    if not chunks:
        sys.exit("no markdown corpus found under docs/")
    corpus = [tokenize(c[1]) for c in chunks]
    return chunks, BM25Okapi(corpus)


def search(query: str, top: int) -> list[dict]:
    from rapidfuzz import fuzz  # type: ignore

    chunks, bm25 = build_index()
    q_tokens = tokenize(query)
    scores = bm25.get_scores(q_tokens) if q_tokens else [0.0] * len(chunks)

    q_low = query.lower()
    results: list[dict] = []
    for (cid, text, line), s in zip(chunks, scores):
        # fuzzy boost: near-miss phrasing, renames, singular/plural drift
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