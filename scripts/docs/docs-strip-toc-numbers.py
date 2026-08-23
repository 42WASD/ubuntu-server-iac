#!/usr/bin/env python3
"""One-time migration: strip hardcoded phase/part prefixes from Contents lists.

The part/section index pages carry a hand-written `## Contents` list whose link
text embeds the phase number, e.g.:

    - [Phase 0 — create the infrastructure repository first](.../index.md)

Now that phase/part numbers are DERIVED from the SSOT manifest (they appear in
the generated nav), these hardcoded prefixes in the Contents lists would drift.
This script removes `Part N — ` / `Phase N — ` / `Phase X — ` prefixes from the
link text of every markdown list item inside these Contents sections, leaving
the clean title only.

Run:
    python3 scripts/docs/docs-strip-toc-numbers.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REF = REPO / "docs" / "reference-design"

# Matches "- [Part 13 — " / "- [Phase 0 — " / "- [Phase A — " link-text prefixes.
LINK_PREFIX = re.compile(
    r"^(\s*-\s+\[)(?:(?:Part|Phase)\s+(?:[IVXLCDM]+|\d+|[A-Z])\s*[\u2014-]\s*)",
    re.MULTILINE,
)


def strip_toc(text: str) -> str:
    return LINK_PREFIX.sub(r"\1", text)


def main() -> int:
    changed = 0
    for md in REF.rglob("index.md"):
        original = md.read_text()
        new = strip_toc(original)
        if new != original:
            md.write_text(new)
            changed += 1
    print(f"Updated {changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())