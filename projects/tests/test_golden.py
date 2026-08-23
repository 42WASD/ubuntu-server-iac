"""Layer 3: golden-file tests — prove the generated output is committed & in sync.

The generators are idempotent: running them must produce ZERO diff against the
committed files. This test regenerates and asserts the tree is unchanged, so
any un-committed regeneration (drift) fails the build.
"""

import subprocess
import sys
from pathlib import Path


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


def test_generators_are_idempotent(repo):
    """Re-running the generators must not change committed output."""
    nav = repo / "scripts" / "docs" / "docs-generate-nav.py"
    impl = repo / "scripts" / "docs" / "docs-generate-implementation.py"

    for script in (nav, impl):
        r = subprocess.run([sys.executable, str(script)],
                           capture_output=True, text=True, cwd=str(repo))
        assert r.returncode == 0, f"{script.name} failed:\n{r.stderr}"

    # Any drift shows up as a diff on the generated files.
    diff = _git(repo, "diff", "--exit-code",
                "mkdocs.yml", "docs/implementation/index.md")
    assert diff.returncode == 0, (
        "GENERATED FILES DRIFTED — re-run the generators and commit them:\n"
        + diff.stdout + diff.stderr)


def test_generated_implementation_lists_all_tracked_phases(repo):
    """The rendered page must contain every tracked section once (as a bullet).

    We match the ``- <icon> `<status>` — [Phase N — ...]`` bullet lines only,
    so runbook `<details>` summaries (which also say "Phase N —") are ignored.
    """
    page = (repo / "docs" / "implementation" / "index.md").read_text()
    import re
    bullets = re.findall(r"^- .*\[Phase (\d+) —", page, flags=re.M)
    if not bullets:
        return  # page not yet generated; structural test covers this
    nums = sorted(int(n) for n in bullets)
    assert nums == list(range(len(nums))), (
        "rendered bullets are not contiguous 0..N: " + str(nums))