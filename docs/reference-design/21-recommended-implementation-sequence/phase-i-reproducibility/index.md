# reproducibility

Once everything is proven:

```text
Ansible all manual host steps
Autoinstall clean OS
OpenTofu external infrastructure
disaster restore test
add build01
add future worker
```

That is when the architecture becomes truly reusable.

## Keeping the docs honest: the doc-impact check

Reproducibility depends on the runbooks staying true to reality. Whenever new
implementing commands run on the host or cluster, documented claims can
silently drift (a VG renamed, a workload scaled, a config file moved).

The check is **declarative**: each documented claim is one entry in
`scripts/docs/doc-impact/live-expectations.yaml` (probe type, expected live
value, docs to fix). A pytest engine (`projects/tests/test_doc_impact.py`,
using testinfra — the standard server-state assertion tooling) turns every
entry into a test; failing tests name the docs to update.

```bash
cd projects
uv run pytest tests/test_doc_impact.py -q -m quick   # ~2s host-only battery
uv run pytest tests/test_doc_impact.py -q            # + cluster & VPS probes
```

Rules of the road (see AGENTS.md): run it after any successful implementing
commands; fix the listed docs in the same turn until green; when a new
persistent fact gets documented, add a YAML entry — no code. Full
doc-vs-reality sweeps are recorded as runbook entries so the reconciliation
itself stays traceable.

---
