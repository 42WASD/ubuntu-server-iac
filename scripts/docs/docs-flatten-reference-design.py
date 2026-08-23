#!/usr/bin/env python3
"""Flatten reference-design into a single linear, chronological sequence.

Background
----------
The reference design was previously split into three groups
(background/build/reference) which scrambled the canonical reading order
(Parts I..XXV). This script:

  1. Moves every part folder up to docs/reference-design/ (parts keep their
     NN-slug, which already sorts by Roman numeral I..XXV).
  2. Renames each section folder to a pure semantic slug (drops the numeric
     prefix that previously encoded order into the filename).
  3. Injects `order: N` frontmatter into every part/section index.md so the
     generators can order by frontmatter instead of filename.
  4. Resolves the known phase-number collisions by renumbering the two game
     additions to a clean tail.

Runbook/progress.yaml key migration is handled separately; this script only
touches the reference-design tree.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: uv add pyyaml (in projects/)", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parent.parent.parent
REF = REPO / "docs" / "reference-design"

GROUPS = ["background", "build", "reference"]

# Resolve the two phase-number collisions. Key = current section-relative path
# (part-dir/current-section-dir), value = new global order.
RENUMBER = {
    "13-game-networking-foundation/03-67-phase-56-minecraft-server-performance": 69,
    "13-game-networking-foundation/04-78-phase-69-game-server-orchestration-operator": 70,
}


def split_section(name: str) -> tuple[int | None, str]:
    """Return (order, semantic_slug) for a section dir name.

    - build phases `NN-GG-phase-N-slug`  -> order = N, slug = slug
    - other sections `NN-GG-slug`        -> order = NN, slug = slug
    - other sections `NN-slug`           -> order = NN, slug = slug
    """
    m = re.match(r"^(\d+)-\d+-phase-(\d+)-(.*)$", name)
    if m:
        return int(m.group(2)), m.group(3)
    m = re.match(r"^(\d+)-(\d+)-(.*)$", name)
    if m:
        return int(m.group(1)), m.group(3)
    m = re.match(r"^(\d+)-(.*)$", name)
    if m:
        return int(m.group(1)), m.group(2)
    return None, name


def read_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            try:
                return (yaml.safe_load(parts[1]) or {}), parts[2]
            except Exception:
                pass
    return {}, text


def write_order(index_md: Path, order: int | None) -> None:
    """Inject `order: N` frontmatter into a page, preserving existing keys."""
    if order is None:
        return
    text = index_md.read_text()
    fm, body = read_frontmatter(text)
    fm["order"] = order
    if body and not body.startswith("\n"):
        body = "\n" + body
    new = "---\n" + yaml.safe_dump(fm, sort_keys=False).rstrip() + "\n---\n" + body
    if new != text:
        index_md.write_text(new)


def main() -> int:
    if not REF.exists():
        print(f"Missing {REF}", file=sys.stderr)
        return 1

    parts = []
    for g in GROUPS:
        gdir = REF / g
        if gdir.is_dir():
            for p in sorted(x for x in gdir.iterdir() if x.is_dir()):
                parts.append((g, p))

    n_sections = 0
    n_subs = 0
    n_moved = 0

    for group, part_dir in parts:
        roman_num = int(part_dir.name.split("-")[0])

        for sec in sorted(x for x in part_dir.iterdir() if x.is_dir()):
            order, slug = split_section(sec.name)
            key = f"{part_dir.name}/{sec.name}"
            if key in RENUMBER:
                order = RENUMBER[key]
            idx = sec / "index.md"
            if idx.exists():
                write_order(idx, order)
                n_sections += 1
            for i, sub in enumerate(sorted(x for x in sec.iterdir() if x.is_dir())):
                sub_idx = sub / "index.md"
                if sub_idx.exists():
                    sub_order, _ = split_section(sub.name)
                    write_order(sub_idx, sub_order)
                    n_subs += 1
            if slug != sec.name:
                shutil.move(str(sec), str(sec.with_name(slug)))

        write_order(part_dir / "index.md", roman_num)

        dest = REF / part_dir.name
        if part_dir != dest:
            shutil.move(str(part_dir), str(dest))
            n_moved += 1

    for g in GROUPS:
        gdir = REF / g
        if gdir.is_dir() and not any(gdir.iterdir()):
            gdir.rmdir()
            print(f"Removed empty group dir: {g}")

    print(
        f"Processed {len(parts)} parts; moved {n_moved}; "
        f"added order frontmatter to {n_sections} sections (+{n_subs} sub-sections)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())