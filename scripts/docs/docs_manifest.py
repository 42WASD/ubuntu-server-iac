#!/usr/bin/env python3
"""Shared loader for the reference-design reading-order manifest.

The manifest at docs/reference-design/_sequence.yaml is the SINGLE SOURCE OF
TRUTH (SSOT) for the reading order of the reference design. Both generators
(docs-generate-nav.py and docs-generate-implementation.py) import this module
to load it and to DERIVE the display numbering:

  - Part numeral (I, II, III ...)  from a part's position in `parts`
  - Phase number                   from a tracked section's global position
  - tracked (build) vs untracked   from the `tracked:` flag in the manifest

Numbers are never stored in page files, so they can never drift or collide.
"""

from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


REPO = Path(__file__).resolve().parent.parent.parent
MANIFEST = REPO / "docs" / "reference-design" / "_sequence.yaml"


def _roman(n: int) -> str:
    """Convert a 1-based integer to a Roman numeral."""
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    out = ""
    for value, sym in vals:
        while n >= value:
            out += sym
            n -= value
    return out


def load_sequence() -> list[dict]:
    """Load and normalize the manifest into:
        [{slug, numeral, tracked, sections: [{slug, subsections: [...]}]}]
    where `sections` are the DIRECT child folders in order, and `numeral` is the
    part's Roman numeral (I, II, ...) derived from its position.
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    data = yaml.safe_load(MANIFEST.read_text())
    parts = []
    for idx, item in enumerate(data["parts"], start=1):
        for slug, meta in item.items():
            parts.append({
                "slug": slug,
                "numeral": _roman(idx),
                "tracked": bool(meta.get("tracked", False)),
                "sections": [_norm_section(s) for s in meta.get("sections", [])],
            })
    return parts


def _norm_section(entry) -> dict:
    """Normalize a section entry (string or {slug: {subsections}})."""
    if isinstance(entry, str):
        return {"slug": entry, "subsections": []}
    for slug, meta in entry.items():
        return {
            "slug": slug,
            "subsections": [_norm_section(s) for s in meta.get("subsections", [])],
        }
    raise ValueError(f"Bad section entry: {entry}")


def assign_phase_numbers(parts: list[dict]) -> None:
    """In-place: set `phase` on every top-level section of tracked parts.

    The phase number is the section's GLOBAL position across all tracked parts,
    so it is contiguous and collision-free by construction.
    """
    counter = 0
    for p in parts:
        if not p["tracked"]:
            continue
        for s in p["sections"]:
            s["phase"] = counter
            counter += 1


def phase_by_slug(parts: list[dict], part_slug: str, section_slug: str):
    """Return the derived phase number for a tracked section, or None."""
    for p in parts:
        if p["slug"] != part_slug:
            continue
        for s in p["sections"]:
            if s["slug"] == section_slug:
                return s.get("phase")
    return None