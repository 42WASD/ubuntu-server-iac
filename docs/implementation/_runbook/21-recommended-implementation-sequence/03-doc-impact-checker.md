---
phase: 21-recommended-implementation-sequence/phase-i-reproducibility
---

# Doc-impact checker — keep runbooks honest after live commands

**Intent:** prevent doc drift structurally. Runbooks record live-state claims;
whenever new implementing commands run, the claims can silently go stale
(VG renamed, workload scaled, config file moved). This adds a fast, read-only
probe battery that compares documented claims with live host/cluster state and
lists exactly which docs need an edit.

**Background (researched 2026-08):** the established tooling for asserting
live server state is **pytest + testinfra** (the standard in the
Ansible/Molecule ecosystem — Ruby's Serverspec equivalent). Drift-detection
suites (driftctl, Argo/KubeDiff, Steampipe) target IaC-vs-live, not
docs-vs-live, so the right shape here is: **declarative expectations
(`live-expectations.yaml`) + a small pytest engine** — adding a check is a
YAML entry, not code. An earlier hand-rolled bash version was replaced after
one iteration because every probe was hardcoded shell logic; the pytest form
also plugs into the existing `uv run pytest` verification flow and gets
pytest's reporting/skips/-k filtering for free.

## Implementation

- `scripts/docs/doc-impact/live-expectations.yaml` — one entry per documented
  claim: probe type (`command`, `file_contains`, `service_active`,
  `swap_active`, `vg_present`, `kubectl_json`, `nodeport_owner`, `ssh`),
  expected value, docs-to-fix list, `quick` flag.
- `projects/tests/test_doc_impact.py` — engine: generates one pytest test per
  YAML entry; uses testinfra for host probes when installed, plain subprocess
  fallback otherwise; networked probes (kubectl/SSH) auto-skip when the target
  is unreachable.
- `conftest.py` — tags tests with the `quick` marker per YAML, so
  `-m quick` runs the host-only battery (~2s) and the full suite adds
  cluster + VPS probes.
- `AGENTS.md` — "Doc-impact" rule: run `-m quick` after any successful
  implementing commands; fix the named docs same-turn; extend the YAML when
  new persistent facts are documented.

## Commands

```bash
cd projects
uv sync                                                  # once (adds testinfra)
uv run pytest tests/test_doc_impact.py -q -m quick       # fast battery
uv run pytest tests/test_doc_impact.py -q                # full probe
```

Current coverage (15 checks): swap, ip_forward, inotify x2, journald bound,
VGs x3, fancontrol, node-alpha Ready, Argo apps Healthy, SC→VG x2, nodePort
30079 owner, relay-VPS NAT persistence. First pytest run caught two probe
bugs (sudo -E rejection → `sudo KUBECONFIG=...` prefix form; kubectl jsonpath
can't reach `.parameters` → Python-side `_dig` path resolution) before going
green.

## Probe-authoring notes

- Expectation values are compared as strings; a trailing `*` means
  startswith (e.g. `vg_k8s_nvme.*` matches the literal live value).
- `ready` is a special dotted key resolving the Node `Ready` condition.
- kubectl must run as `sudo KUBECONFIG=/etc/rancher/rke2/rke2.yaml kubectl ...`
  (env-preserving `sudo -E` is rejected in non-tty contexts).
