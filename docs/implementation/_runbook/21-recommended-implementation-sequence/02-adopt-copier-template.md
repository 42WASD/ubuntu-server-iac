# Copier template adoption — establish `.copier-answers.yml`

**Intent:** enable `copier update` on this repo for future template syncs.

`copier update` requires a `.copier-answers.yml` (records template source +
commit + answers). This repo had never been `copier copy`-ed — its toolkit was
merged by hand — so `copier update` failed with `TypeError: Template not found`.
The only supported way to establish the answers file is a real `copier copy`
adoption.

**What changed:**
1. Ran `copier copy` from `42WASD/template-docs-project` over the working tree.
2. Answered `No` to every conflict where iac's file is the richer, project-
   specific version (toolkit scripts, nav generator, `_sequence.yaml`,
   `mkdocs.yml`, `AGENTS.md`, docs pages) so nothing valuable was clobbered.
3. Restored 6 files that were accidentally overwritten with generic template
   content (`git checkout HEAD -- ...`) — only the two genuinely-new additions
   were kept.
4. Removed the template's generic example scaffold pages
   (`01-understand-the-system/`, `02-step-by-step-implementation/`) that would
   collide with iac's real numbered phases.
5. Kept `README.md` (iac had none) and `.copier-answers.yml` (essential for
   future `copier update`).

**Commands run (adoption):**
```bash
# Copier adoption over preexisting tree (answer prompts interactively;
# keep iac's files where it differs)
copier copy --defaults \
  --data project_name=ubuntu-server-iac \
  --data project_slug=ubuntu-server-iac \
  --data org=42WASD \
  --data author=jya0 \
  gh:42WASD/template-docs-project .

# Restore files that generic template clobbered (iac's versions are richer)
git checkout HEAD -- \
  AGENTS.md \
  docs/implementation/progress.yaml \
  docs/reference-design/_sequence.yaml \
  docs/stylesheets/extra.css \
  projects/pyproject.toml \
  scripts/docs/README.md

# Remove generic template example pages (collide with iac's real phases)
rm -rf docs/reference-design/01-understand-the-system \
       docs/reference-design/02-step-by-step-implementation

# Commit + push (no CI: workflow is path-filtered to docs/ + mkdocs.yml)
git add .copier-answers.yml README.md
git commit -m "adopt template via copier copy (establish .copier-answers.yml for future updates)"
git push origin main
```

**Verified:**
- `docs/verify.sh` toolkit byte-identical to template (`verify.sh`,
  `docs_manifest.py`, `docs-generate-implementation.py`).
- `uv run mkdocs build -M -f ../mkdocs.yml` builds clean.
- `.copier-answers.yml` present with `_commit` + answers (never hand-edited).
- `git push` → `main` at `c5264cf`; CI not re-run (no docs/mkdocs change).

> **Future template sync:** now that `.copier-answers.yml` exists, use
> `copier update .` to pull in the next template revision.
---

# Appendix (2026-08-29): full doc-reality sweep via committed index

**Method:** pytest live-state battery first (15/15 pass), then ~25 hybrid
index searches (`impact_search.py`) over every platform area, verifying the
top hits' claims against live host/cluster state.

**Discrepancies found and fixed:**

1. **OIDC issuer naming (ref 27)** — reference page still showed the
   `dex.alpha.taild82ced.ts.net` subdomain idea; the implemented design (and
   runbook) uses the node FQDN `alpha.taild82ced.ts.net` because Tailscale
   certs cover only the node's own name. Ref page corrected.
2. **Metrics stack undocumented (part 08)** — kube-prometheus-stack-88.5.4
   deployed 2026-08-24 via plain Helm (not Argo, no PVCs, no retention
   override, no Loki) with zero runbook/progress records. Added
   `_runbook/08-monitoring-and-logs/00-metrics-stack.md` (as-deployed record
   + follow-ups), progress key `in-progress`, and an as-deployed note on the
   reference page.
3. **NVIDIA DKMS kernel version (ph12)** — recorded `7.0.0-29`; live is
   `7.0.0-30` (auto-rebuilt on kernel update). Runbook updated with the
   rebuild-on-upgrade note.
4. **SSH hardening status (ref 03)** — reference presented the baseline as
   if applied; the phase is `deferred` and live sshd is stock
   (`passwordauthentication yes`). Added an explicit "Status on alpha: NOT
   applied" section with live values.

**Verified coherent (no action):** PriorityClass values (incl. prod-high
20000), kubelet reservations (system 12/24Gi/20Gi, kube 2/4Gi/10Gi,
evictionHard 8Gi/12%/15%), netplan static .240, developer limits (systemd
user slices — Ansible-rendered comments differ, values identical), quotas,
OpenEBS SC→VG mapping, etcd snapshots, OIDC flags, fan control, Cilium
kube-proxy-replacement=true, RBAC subjects.

**Part-status correction:** parts 08 (metrics running), 09 (Harbor not
installed), 10 (Skaffold/BuildKit absent), 12 (no GPU operator), 14
(snapshots local only, no offsite) remain correctly `not-started`/partial in
progress.yaml — their reference pages describe intent, not state.
