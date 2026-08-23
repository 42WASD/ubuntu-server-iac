"""Layer 1+2: deterministic structural validation of the SSOT manifest.

These tests codify the invariant checks that used to be done by hand:
duplicate slugs, missing pages, tracked-part sanity, phase continuity, and
duplicate runbook keys. They run fast and are fully deterministic.
"""

import re
from pathlib import Path

import docs_manifest as dm


def test_validation_returns_no_errors(parts, repo):
    """The committed manifest+disk must be structurally valid (regression)."""
    assert dm.validate(parts, repo) == []


def test_no_duplicate_runbook_phase_keys(repo):
    """Every _runbook file must have a unique phase: key (Layer 1)."""
    errors = dm.validate_runbooks(repo)
    assert errors == [], "\n".join(errors)


def test_phase_numbers_contiguous(parts):
    """Tracked top-level sections must be contiguous 0..N with no gaps."""
    phases = [s["phase"] for p in parts if p["tracked"]
              for s in p["sections"]]
    assert phases == list(range(len(phases))), f"phase gap: {phases}"


def test_every_part_has_one_number_free_h1(repo):
    """No index.md H1 may carry a derived-number prefix (Part N/Phase N/roman).

    Numbers are derived by the generators from the manifest, never stored in
    pages, so a number-prefixed H1 signals stale hand-editing that fights the
    SSOT.
    """
    ref = repo / "docs" / "reference-design"
    bad = []
    for md in sorted(ref.rglob("index.md")):
        text = md.read_text()
        for line in re.findall(r"^#\s+(.+)$", text, flags=re.M):
            if re.match(r"^(Part|Phase)\s+[IVX\d]+[—\-:]", line):
                bad.append(f"{md}: number-prefixed H1 '{line}'")
    assert bad == [], "\n".join(bad)


def test_every_progress_key_maps_to_manifest(repo):
    """Every progress.yaml key must resolve to a manifest section path.

    This catches STALE keys left over after a reorder/rename — they'd silently
    stop being rendered, and the phase's true status would be lost.
    """
    progress = _load_progress(repo)
    parts = dm._load_from_repo(repo)
    valid = set()
    for p in parts:
        valid.add(p["slug"])
        for slug, path in dm._iter_paths(p["sections"], p["slug"]):
            valid.add(path)
    stale = [k for k in progress if k not in valid]
    assert stale == [], "stale progress.yaml keys: " + ", ".join(stale)


def _load_progress(repo):
    import yaml
    p = repo / "docs" / "implementation" / "progress.yaml"
    return yaml.safe_load(p.read_text()) or {} if p.exists() else {}