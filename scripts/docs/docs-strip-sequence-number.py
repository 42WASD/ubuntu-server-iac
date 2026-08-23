#!/usr/bin/env python3
"""One-time migration: strip hardcoded ordering/numbering from reference-design pages.

After this repo moved ordering into the SSOT manifest
(docs/reference-design/_sequence.yaml), the per-page `order:` and `tracked:`
frontmatter keys and the `Part N —`/`Phase N —` prefixes in H1 headings are
redundant and can drift. This script removes them so that numbering is derived
ONLY from the manifest.

What it does per reference-design index.md:
  1. Removes `order:` and `tracked:` keys from YAML frontmatter (if present).
  2. Strips a leading `Part <Roman|Number> — ` or `Phase <Num> — ` or
     `Phase <Letter> — ` prefix from the H1.

Run:
    python3 scripts/docs/docs-strip-sequence-from-pages.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REF = REPO / "docs" / "reference-design"

H1_PREFIX = re.compile(
    r"^#\s+(?:(?:Part|Phase)\s+(?:[IVXLCDM]+|\d+|[A-Z])\s*[\u2014-]\s*)",
    re.MULTILINE,
)


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) != 3:
        return text
    fm, body = parts[1], parts[2]
    lines = []
    changed = False
    for line in fm.splitlines():
        if re.match(r"^\s*(order|tracked)\s*:", line):
            changed = True
            continue  # drop it
        lines.append(line)
    new_fm = "\n".join(lines).strip()
    if not new_fm:
        # Frontmatter became empty; drop the delimiters entirely.
        return body.lstrip("\n")
    return f"---\n{new_fm}\n---\n{body}"


def strip_h1(text: str) -> str:
    new = H1_PREFIX.sub("# ", text)
    return new


def main() -> int:
    changed = 0
    for md in REF.rglob("index.md"):
        if md.name.startswith("_") or "_sequence" in str(md):
            continue
        original = md.read_text()
        new = strip_frontmatter(original)
        new = strip_h1(new)
        if new != original:
            md.write_text(new)
            changed += 1
    print(f"Updated {changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())