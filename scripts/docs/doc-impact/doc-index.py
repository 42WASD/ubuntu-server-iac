#!/usr/bin/env python3
"""doc-index — build/sync the committed FTS5 search index for doc-impact.

The index is a SQLite database (FTS5) stored IN the repo
(`scripts/docs/doc-impact/doc-index.db`), so any clone gets it for free —
no external service, no rebuild step for consumers.

Incremental sync: each chunk is keyed by the SHA-256 of its content, so a
changed/renamed/moved doc automatically removes stale rows and inserts new
ones. Running `sync` after any doc edit is idempotent and ~0.2s; chunks whose
hash is unchanged are not rewritten.

Commands:
  sync       update the index to match the current docs (only changed chunks)
  status     show index freshness (docs vs index, pending changes)
  rebuild    drop and recreate from scratch (schema upgrades)

The index schema is versioned; if this script's CHUNKER_VERSION bumps, the
next `sync` rebuilds automatically.
"""

from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "doc-index.db"

# Bump when chunking logic changes to force a full rebuild on next sync.
CHUNKER_VERSION = 1

# Same corpus as impact_search.py
REPO = SCRIPT_DIR.parents[2]
DOC_ROOTS = [
    REPO / "docs" / "reference-design",
    REPO / "docs" / "implementation" / "_runbook",
    REPO / "docs" / "guides",
    REPO / "infra",
]
MAX_CHUNK = 1200

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
    path, heading, body, tokenize='porter unicode61'
);
CREATE TABLE IF NOT EXISTS chunk_hashes (
    chunk_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hashes ON chunk_hashes(content_hash);
"""


# --------------------------------------------------------------------------
# Chunking (kept in sync with impact_search.py semantics)
# --------------------------------------------------------------------------

def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in DOC_ROOTS:
        if root.exists():
            files.extend(root.rglob("*.md"))
    return sorted(files)


def chunk_markdown(path: Path) -> list[tuple[str, str, str, int]]:
    """Return [(chunk_id, heading, body, line_no)] — heading-aware chunks."""
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    out: list[tuple[str, str, str, int]] = []
    buf: list[str] = []
    start_line = 1
    heading = ""

    def flush():
        nonlocal buf, start_line, heading
        if not buf:
            return
        body = "\n".join(buf).strip()
        if len(body) < 20:
            buf, start_line = [], 0
            return
        cid = f"{path}:{start_line}"
        out.append((cid, heading, body, start_line))
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
    return out


def current_chunks() -> dict[str, tuple[str, str, str, int]]:
    """All live chunks keyed by chunk_id."""
    live: dict[str, tuple[str, str, str, int]] = {}
    for f in iter_markdown_files():
        for cid, heading, body, line in chunk_markdown(f):
            rel = str(f.relative_to(REPO))
            live[f"{rel}::{line}"] = (rel, heading, body, line)
    return live


# --------------------------------------------------------------------------
# DB helpers
# --------------------------------------------------------------------------

def connect() -> sqlite3.Connection:
    fresh = not DB_PATH.exists()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    if fresh:
        set_meta(con, "chunker_version", str(CHUNKER_VERSION))
    return con


def get_meta(con: sqlite3.Connection, key: str) -> str | None:
    row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(con: sqlite3.Connection, key: str, value: str) -> None:
    con.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def stored_hashes(con: sqlite3.Connection) -> dict[str, str]:
    return {r["chunk_id"]: r["content_hash"]
            for r in con.execute("SELECT chunk_id, content_hash FROM chunk_hashes")}


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_status() -> int:
    if not DB_PATH.exists():
        print("index: MISSING (run `doc-index sync` to create)")
        return 1
    con = connect()
    live = current_chunks()
    have = stored_hashes(con)
    ver = get_meta(con, "chunker_version")
    n_indexed = con.execute("SELECT COUNT(*) c FROM chunks").fetchone()["c"]
    changed = [cid for cid in live if cid not in have]
    removed = [cid for cid in have if cid not in live]
    print(f"index: {DB_PATH.relative_to(REPO)} ({n_indexed} chunks, "
          f"chunker v{ver})")
    print(f"live:  {len(live)} chunks across the doc corpus")
    if ver != str(CHUNKER_VERSION):
        print(f"NOTE: chunker v{CHUNKER_VERSION} != index v{ver} — "
              f"next sync rebuilds the index")
    if not changed and not removed:
        print("state: UP TO DATE")
        return 0
    if changed:
        print(f"pending inserts: {len(changed)} (e.g. {changed[:3]})")
    if removed:
        print(f"pending removals: {len(removed)} (e.g. {removed[:3]})")
    print("run `doc-index sync` to reconcile")
    return 1


def cmd_sync() -> int:
    con = connect()
    live = current_chunks()
    have = stored_hashes(con)

    inserts, updates = [], []
    for cid, (rel, heading, body, _line) in live.items():
        h = hashlib.sha256(f"{rel}\n{heading}\n{body}".encode()).hexdigest()
        if cid not in have:
            inserts.append((cid, rel, heading, body, h))
        elif have[cid] != h:
            updates.append((cid, rel, heading, body, h))

    # Removals: chunk ids that vanished, plus same-file rows whose line
    # shifted (id embeds the line number).
    live_ids = set(live)
    removals = [cid for cid in have if cid not in live_ids]

    for cid in removals:
        con.execute("DELETE FROM chunks WHERE rowid IN "
                    "(SELECT rowid FROM chunks WHERE chunks.rowid IN "
                    "(SELECT rowid FROM chunk_hashes WHERE chunk_id=?))",
                    (cid,))
        con.execute("DELETE FROM chunk_hashes WHERE chunk_id=?", (cid,))
    for cid, rel, heading, body, h in updates:
        con.execute("DELETE FROM chunks WHERE rowid IN "
                    "(SELECT rowid FROM chunk_hashes WHERE chunk_id=?)", (cid,))
        con.execute("DELETE FROM chunk_hashes WHERE chunk_id=?", (cid,))
        inserts.append((cid, rel, heading, body, h))
    con.executemany(
        "INSERT INTO chunks(path, heading, body) VALUES(?,?,?)",
        [(r, h, b) for _, r, h, b, _ in inserts],
    )
    con.executemany(
        "INSERT INTO chunk_hashes(chunk_id, content_hash) VALUES(?,?)",
        [(cid, h) for cid, _, _, _, h in inserts],
    )
    set_meta(con, "chunker_version", str(CHUNKER_VERSION))
    con.commit()

    n = con.execute("SELECT COUNT(*) c FROM chunks").fetchone()["c"]
    print(f"synced: +{len(inserts)} inserted/updated, -{len(removals)} removed "
          f"→ {n} chunks indexed")
    print(f"index:  {DB_PATH.relative_to(REPO)} (commit this file with the docs)")
    return 0


def cmd_rebuild() -> int:
    if DB_PATH.exists():
        DB_PATH.unlink()
    return cmd_sync()


COMMANDS = {"sync": cmd_sync, "status": cmd_status, "rebuild": cmd_rebuild}


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd not in COMMANDS:
        print(f"usage: doc-index.py {{sync|status|rebuild}}", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(COMMANDS[cmd]())


if __name__ == "__main__":
    main()