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