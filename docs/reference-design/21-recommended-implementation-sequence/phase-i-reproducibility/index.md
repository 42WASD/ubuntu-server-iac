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
silently drift (a VG renamed, a workload scaled, a config file moved). The
check is a three-step loop:

**1. Smart diff — find the docs a change touches.** A search over a
**committed FTS5 index** (SQLite, `scripts/docs/doc-impact/doc-index.db`)
maps a free-text change summary onto the runbook/reference pages that talk
about the same things — even when wording differs. The index ships in the
repo (clones get it free) and self-updates: a post-commit hook resyncs it
whenever a commit touches `docs/` or `infra/`, so changed/renamed docs
automatically replace their indexed parts.

```bash
cd projects
uv run python ../scripts/docs/doc-impact/impact_search.py \
  "scaled minecraft-demo to 0, prod velocity now owns nodePort 30079"
```

**2. Reconcile.** Load each hit, compare its claims against what actually
changed, and edit whatever is stale — in the same turn.

**3. Regression battery — deterministic claims.** Every known persistent
claim is also a declarative entry in
`scripts/docs/doc-impact/live-expectations.yaml`, asserted live by
`projects/tests/test_doc_impact.py` (pytest + testinfra):

```bash
uv run pytest tests/test_doc_impact.py -q -m quick   # ~2s host-only battery
uv run pytest tests/test_doc_impact.py -q            # + cluster & VPS probes
```

Adding a new claim = one YAML entry, no code. Failing tests name the docs to
fix. Full doc-vs-reality sweeps (like the 2026-08-29 audit) are recorded as
runbook entries so the reconciliation itself stays traceable.

---
