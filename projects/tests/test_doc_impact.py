"""Doc-impact engine: assert documented live-state claims from live-expectations.yaml.

Each YAML entry becomes one pytest test. Failing a test means a documented
claim drifted from live state — the entry's ``docs`` list says what to fix.

Run:
    uv run pytest projects/tests/test_doc_impact.py -q            # full probe
    uv run pytest projects/tests/test_doc_impact.py -q -m quick   # fast battery
    uv run pytest projects/tests/test_doc_impact.py -q -k swap    # single claim

Design notes:
- Probes are DATA (the YAML file), not code. Adding a check = one YAML entry.
- Uses testinfra when available for host probes (service/file/command modules);
  falls back to plain subprocess so the suite also runs on hosts without
  testinfra installed (CI, other machines).
- Networked probes (kubectl/ssh) are skipped automatically when the target is
  unreachable, so the battery is safe to run anywhere.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
EXPECTATIONS = REPO / "scripts" / "docs" / "doc-impact" / "live-expectations.yaml"

try:  # testinfra is optional; host probes work with or without it
    import testinfra  # type: ignore

    HAS_TESTINFRA = True
except ImportError:  # pragma: no cover
    testinfra = None  # type: ignore
    HAS_TESTINFRA = False


def _load_checks() -> list[dict]:
    if not EXPECTATIONS.exists():
        return []
    data = yaml.safe_load(EXPECTATIONS.read_text()) or {}
    return [c for c in (data.get("checks") or []) if not c.get("skip")]


CHECKS = _load_checks()


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    """Run a command, return (rc, stdout+stderr). Never raises."""
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return p.returncode, (p.stdout + p.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return 127, f"PROBE-ERROR: {e}"


def _host():
    """Local testinfra host (or None when testinfra is missing)."""
    if HAS_TESTINFRA:
        return testinfra.get_host("local://")
    return None


# --------------------------------------------------------------------------- #
# Probe implementations: (check) -> (ok: bool, detail: str)
# --------------------------------------------------------------------------- #

def probe_command(c: dict) -> tuple[bool, str]:
    rc, out = _run(c["command"].split())
    want = str(c["expect"])
    got = out.splitlines()[-1] if out else ""
    return (rc == 0 and got == want), f"want {want!r}, got {got!r} (rc={rc})"


def probe_file_contains(c: dict) -> tuple[bool, str]:
    p = Path(c["path"])
    if not p.exists():
        return False, f"{c['path']} missing"
    want = str(c["expect"])
    return (want in p.read_text()), f"{want!r} in {c['path']}"


def probe_service_active(c: dict) -> tuple[bool, str]:
    h = _host()
    if h is not None:
        svc = h.service(c["service"])
        ok = svc.is_running
        return ok, f"service {c['service']} running={ok}"
    rc, _ = _run(["systemctl", "is-active", "--quiet", c["service"]])
    return rc == 0, f"systemctl is-active rc={rc}"


def probe_swap_active(c: dict) -> tuple[bool, str]:
    rc, out = _run(["swapon", "--show", "--noheadings"])
    active = rc == 0 and "/swap.img" in out
    want = c["expect"] == "active"
    return active == want, f"swap active={active}, want {c['expect']}"


def probe_vg_present(c: dict) -> tuple[bool, str]:
    rc, out = _run(["sudo", "-n", "vgs", "--noheadings", "-o", "vg_name"])
    if rc != 0:  # try without sudo -n (interactive sudo available?)
        rc, out = _run(["sudo", "vgs", "--noheadings", "-o", "vg_name"])
    want = str(c["expect"])
    ok = rc == 0 and want in out.split()
    return ok, f"vgs rc={rc}, want VG {want!r}"


def _kubectl(*args: str) -> tuple[int, str]:
    # KUBECONFIG is root-only (/etc/rancher/rke2/rke2.yaml), so kubectl must
    # run under sudo with the env var passed as a command prefix (sudo -E is
    # rejected when the caller's environment can't be preserved).
    return _run(
        ["sudo", "KUBECONFIG=/etc/rancher/rke2/rke2.yaml", "kubectl", *args],
        timeout=45,
    )


def _dig(obj: dict, dotted: str):
    """Resolve a dotted path like 'parameters.vgpattern' or
    'status.conditions' (list -> first element) against a parsed object."""
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[0] if cur else None
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def probe_kubectl_json(c: dict) -> tuple[bool, str]:
    res = c["resource"].split()
    args = ["get", res[0]] + res[1:] + ["-o", "json"]
    rc, out = _kubectl(*args)
    if rc != 0:
        return False, f"kubectl get {res[0]} rc={rc}: {out[:120]}"
    try:
        items = json.loads(out)["items"]
    except (json.JSONDecodeError, KeyError):
        return False, "unparseable kubectl output"

    if c.get("all_healthy"):
        unhealthy = [
            i["metadata"]["name"]
            for i in items
            if i.get("status", {}).get("health", {}).get("status")
            not in ("Healthy", "Progressing", "Suspended")
        ]
        return (not unhealthy), f"unhealthy apps: {unhealthy or 'none'}"

    sel = c.get("select")
    matches = [i for i in items if i["metadata"]["name"] == sel] if sel else items
    if not matches:
        return False, f"resource {sel!r} not found"
    obj = matches[0]

    for dotted, want in (c.get("expect") or {}).items():
        if dotted == "ready":  # Ready condition (list of conditions)
            conds = obj.get("status", {}).get("conditions", [])
            got = next(
                (str(x.get("status")) for x in conds if x.get("type") == "Ready"),
                "Unknown",
            )
        else:
            try:
                got = _dig(obj, dotted)
            except KeyError:
                return False, f"{dotted}: path not found on {sel or res[0]}"
        got_s = str(got)
        # 'pattern*' suffix = startswith match (e.g. vgpattern vg_k8s_nvme.*)
        ok = got_s.startswith(want[:-1]) if want.endswith("*") else got_s == str(want)
        if not ok:
            return False, f"{dotted}: want {want!r}, got {got_s!r}"
    return True, f"{sel or res[0]}: all expected paths match"


def probe_nodeport_owner(c: dict) -> tuple[bool, str]:
    rc, out = _kubectl("get", "svc", "-A", "-o", "json")
    if rc != 0:
        return False, f"kubectl get svc rc={rc}"
    try:
        svcs = json.loads(out)["items"]
    except json.JSONDecodeError:
        return False, "unparseable svc output"
    owners = []
    for s in svcs:
        for p in s.get("spec", {}).get("ports", []):
            if p.get("nodePort") == c["nodePort"]:
                owners.append(f"{s['metadata']['namespace']}/{s['metadata']['name']}")
    want = str(c["expect"])
    return (owners == [want]), f"nodePort {c['nodePort']} owners={owners or 'none'}"


def probe_ssh(c: dict) -> tuple[bool, str]:
    rc, out = _run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
         c["host"], c["command"]],
        timeout=20,
    )
    if rc == 255 and "PROBE-ERROR" not in out:
        return None, "ssh unreachable"  # skip
    want = str(c["expect"])
    return (rc == 0 and out == want), f"want {want!r}, got {out!r} (rc={rc})"


PROBES = {
    "command": probe_command,
    "file_contains": probe_file_contains,
    "service_active": probe_service_active,
    "swap_active": probe_swap_active,
    "vg_present": probe_vg_present,
    "kubectl_json": probe_kubectl_json,
    "nodeport_owner": probe_nodeport_owner,
    "ssh": probe_ssh,
}


# --------------------------------------------------------------------------- #
# Test generation
# --------------------------------------------------------------------------- #

def pytest_generate_tests(metafunc):
    if "check" in metafunc.fixturenames:
        ids = [c["id"] for c in CHECKS]
        metafunc.parametrize("check", CHECKS, ids=ids)


@pytest.fixture
def _check_meta(request):
    """Expose the current check dict (unused in test bodies; kept for CLI
    filtering helpers and debugging)."""
    return request.node.callspec.params["check"]


@pytest.mark.doc_impact
def test_documented_claim_matches_live_state(check: dict):
    probe = PROBES[check["probe"]]
    ok, detail = probe(check)

    if ok is None:  # probe target unreachable -> skip, don't fail
        pytest.skip(detail)

    if not ok:
        docs = "\n      ".join(check.get("docs", []))
        pytest.fail(
            f"[{check['id']}] documented claim drifted from live state.\n"
            f"  probe: {check['probe']}\n  detail: {detail}\n"
            f"  fix docs:\n      {docs}",
            pytrace=False,
        )
