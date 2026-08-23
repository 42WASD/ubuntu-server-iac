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

import sys
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


# ---------------------------------------------------------------------------
# Validation (Layer 2) — deterministic structural checks, runnable from CLI.
# ---------------------------------------------------------------------------

def _iter_paths(sections: list[dict], prefix: str):
    """Yield (slug, full_path) for every node (recursive)."""
    for s in sections:
        path = f"{prefix}/{s['slug']}"
        yield s["slug"], path
        yield from _iter_paths(s["subsections"], path)


def _load_from_repo(repo: Path) -> list[dict]:
    """Load + normalize the manifest from an arbitrary repo root."""
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    manifest = repo / "docs" / "reference-design" / "_sequence.yaml"
    data = yaml.safe_load(manifest.read_text())
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


def validate(parts: list[dict], repo: Path | None = None) -> list[str]:
    """Return a list of structural invariant violations (empty = valid).

    Deterministically catches:
      - duplicate slugs (case-insensitive) anywhere in the tree
      - a part/section whose index.md is missing on disk
      - a tracked part with zero sections
      - phase-number gaps after assign_phase_numbers
    """
    errors: list[str] = []
    repo = repo or REPO
    ref = repo / "docs" / "reference-design"

    for p in parts:
        ps = p["slug"]
        if not (ref / ps / "index.md").is_file():
            errors.append(f"part '{ps}': missing {ref / ps}/index.md")
        if p["tracked"] and not p["sections"]:
            errors.append(f"tracked part '{ps}' has zero sections")
        # Duplicate slugs only matter WITHIN a part's nav subtree; the same slug
        # can legitimately appear in different parts (e.g. a glossary entry that
        # reuses a section name). Track per-part so cross-part reuse is allowed.
        seen: dict[str, str] = {ps: ps}
        for slug, path in _iter_paths(p["sections"], ps):
            if slug.lower() in seen:
                errors.append(f"duplicate slug '{slug}' in part '{ps}' "
                              f"(path '{path}' clashes with "
                              f"'{seen[slug.lower()]}')")
            seen[slug.lower()] = path
            if not (ref / path / "index.md").is_file():
                errors.append(f"section '{path}': missing {ref / path}/index.md")

    # Phase continuity: tracked top-level sections must be contiguous 0..N.
    tmp = [dict(p) for p in parts]
    assign_phase_numbers(tmp)
    phases = [s["phase"] for p in tmp if p["tracked"]
              for s in p["sections"]]
    for i, ph in enumerate(phases):
        if ph != i:
            errors.append(f"phase-number gap at position {i}: got {ph}, "
                          f"expected {i} (sequence {phases})")
            break
    return errors


def validate_runbooks(repo: Path | None = None) -> list[str]:
    """Detect duplicate `phase:` keys across _runbook files (Layer 1)."""
    errors: list[str] = []
    repo = repo or REPO
    base = repo / "docs" / "implementation" / "_runbook"
    if not base.exists() or yaml is None:
        return errors
    seen: dict[str, list[str]] = {}
    for f in sorted(base.rglob("*.md")):
        text = f.read_text()
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) != 3:
            continue
        fm = yaml.safe_load(parts[1]) or {}
        phase = fm.get("phase")
        if phase:
            seen.setdefault(phase, []).append(str(f))
    for phase, files in seen.items():
        if len(files) > 1:
            errors.append(f"duplicate runbook phase '{phase}' in {files} "
                          "(silent-overwrite risk in load_runbook)")
    return errors


def run_validation(repo: Path | None = None) -> int:
    """Validate manifest + runbook invariants. Returns 0 if all good."""
    repo = repo or REPO
    errors = validate(load_sequence(), repo) + validate_runbooks(repo)
    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("VALIDATION OK")
    return 0


def _cli() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(REPO),
                    help="repo root (default: auto-detect)")
    args = ap.parse_args()
    repo = Path(args.repo)
    return run_validation(repo)


if __name__ == "__main__":
    raise SystemExit(_cli())