"""Conftest: shared fixtures for the SSOT validation suite.

Ensures ``scripts/docs`` is importable and points helpers at the repo root
regardless of the working directory.
"""

import sys
from pathlib import Path

import pytest

# Repository root = two levels up from this file (projects/tests/ -> repo).
REPO = Path(__file__).resolve().parent.parent.parent

# Make scripts/docs importable (contains docs_manifest.py).
DOCS_SCRIPTS = REPO / "scripts" / "docs"
if str(DOCS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DOCS_SCRIPTS))

import docs_manifest as dm  # noqa: E402


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO


@pytest.fixture(scope="session")
def parts(repo: Path) -> list[dict]:
    """Loaded + phase-assigned manifest parts for this repo."""
    p = dm._load_from_repo(repo)
    dm.assign_phase_numbers(p)
    return p


@pytest.fixture(scope="session")
def manifest_path(repo: Path) -> Path:
    return repo / "docs" / "reference-design" / "_sequence.yaml"

def pytest_collection_modifyitems(config, items):
    """Tag doc-impact tests with 'quick' per live-expectations.yaml so
    `pytest -m quick` runs just the fast host-only battery."""
    try:
        from test_doc_impact import CHECKS  # module under tests/
    except ImportError:
        return
    by_id = {c["id"]: c for c in CHECKS}
    for item in items:
        callspec = getattr(item, "callspec", None)
        if callspec is None:
            continue
        check = callspec.params.get("check")
        if check and by_id.get(check.get("id"), {}).get("quick"):
            item.add_marker(pytest.mark.quick)
