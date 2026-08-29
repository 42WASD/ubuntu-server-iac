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

### Tool evaluation — why no existing framework was adopted (2026-08-29)

Evaluated the "ready-made" options before/after building the local pipeline:

| Candidate | Verdict | Why |
|---|---|---|
| `jbrockSTL/doc-drift` (GH Action) | Discard | PR-only, sees only git diffs of code (OpenAI-only, ~0 traction). Live-state drift produces no diff — it would fire on nothing. |
| DocDrift / docwatcher (GH Action + local CLI) | Discard | Closest architecturally (local mode, Ollama/Groq support), but its engine extracts changed **code symbols from staged diffs**; our trigger is live state, not code. Would duplicate `impact_search.py` with a second indexing stack. Single maintainer, 5 stars. |
| DeepDocs (GitHub App) | Discard / harmful | Auto-commits doc edits to the repo — collides with the SSOT golden-test discipline (generated output committed together, verify.sh). Cloud credit-metered, can't see the host. |

Decisive criterion: every tool solves **code-vs-docs** drift keyed off git
diffs; this repo's problem is **world-vs-docs** drift driven by commands the
agent runs locally (invisible to git/GitHub until recorded). The deterministic
half (live-state assertions) is strictly stronger as real pytest probes than
as LLM confidence scores; the semantic half (find docs a change touches) is
`impact_search.py`; the missing "fire after live commands, not after commits"
hook exists in no candidate and is exactly the AGENTS.md Doc-impact rule.

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
- `scripts/docs/doc-impact/impact_search.py` — the "smart diff" (step 1 of
  the workflow): hybrid retrieval over the doc corpus (heading-aware chunks,
  per-file dedupe). Given a free-text change summary it returns the
  runbook/reference pages that talk about the same things — even when the
  wording differs (renames, reworded claims). The agent then loads each hit
  and corrects drift (step 2); the pytest battery (step 3) regression-tests
  the deterministic claims.
- `scripts/docs/doc-impact/doc-index.py` — builds/updates the **committed
  FTS5 index** (`doc-index.db`, 1078 chunks, 1.4 MB) so clones get the search
  index for free:
  - `sync` — incremental, per-chunk SHA-256 hash compare: a changed/moved/
    renamed doc removes its stale rows and inserts new ones (~0.2s,
    idempotent; a one-line edit produced exactly `+1` delta).
  - `status` — index freshness; `rebuild` — full recreate (schema/chunker
    version bump forces this automatically).
  - FTS5 (porter+unicode61 tokenizer) is built into SQLite — no service, no
    embedding model, no external dependency.
- `.githooks/post-commit` (+ `scripts/docs/doc-impact/setup-git-hooks.sh`,
  run once per clone) — after any commit touching `docs/` or `infra/`, the
  hook re-syncs the index and **amends the `.db` into the same commit**, so
  the committed index always matches the committed docs. Verified end-to-end:
  doc edit → commit → `doc-index: resynced and amended into commit`; the new
  line is immediately findable via `impact_search.py`.
- `AGENTS.md` — "Doc-impact" rule: impact_search (step 1) → reconcile hits
  (step 2) → pytest battery (step 3) after any successful implementing
  commands; extend the YAML when new persistent facts are documented.

## Commands

```bash
cd projects
uv sync                                                  # once (adds testinfra)
uv run pytest tests/test_doc_impact.py -q -m quick       # fast battery (step 3)
uv run pytest tests/test_doc_impact.py -q                # full probe (step 3)

# smart diff (steps 1-2): find + reconcile docs a change touches
uv run python ../scripts/docs/doc-impact/impact_search.py \
  "scaled minecraft-demo to 0, prod velocity now owns nodePort 30079"
uv run python ../scripts/docs/doc-impact/impact_search.py --json "..."  # machine-readable
```

Retrieval validated against three real historical drifts; each returned the
exact docs that were actually stale:
- "renamed vg_k8s_fast to vg_k8s_nvme, recreated StorageClasses" →
  phase-10-storage, phase-32-storageclasses, storageclasses ref page (top 3)
- "scaled minecraft-demo to 0, service reverted to ClusterIP" →
  minecraft-demo runbook + phase-55 relay runbook
- "kubectl now needs sudo KUBECONFIG" → ph27 auth + ph17 admin-kubeconfig

Current pytest coverage (15 checks): swap, ip_forward, inotify x2, journald
bound, VGs x3, fancontrol, node-alpha Ready, Argo apps Healthy, SC→VG x2,
nodePort 30079 owner, relay-VPS NAT persistence. First pytest run caught two
probe bugs (sudo -E rejection → `sudo KUBECONFIG=...` prefix form; kubectl
jsonpath can't reach `.parameters` → Python-side `_dig` path resolution)
before going green.

## Retrieval notes (impact_search.py + doc-index.py)

- Index: **FTS5** (`porter unicode61`) in a committed SQLite file — chosen
  over embeddings/vector stores deliberately: zero service, zero model,
  instant clone, ~10 ms queries at this corpus size (1078 chunks). Hybrid
  scoring: `bm25(chunks) + 2.5 * rapidfuzz.partial_ratio/100` — lexical finds
  exact terms; fuzzy catches renames/rewording lexical-only misses. (2026
  best practice per Cursor/Sourcegraph: hybrid beats pure-vector at
  small-corpus scale; embeddings pay off only on large stable corpora.)
- FTS5 query building: tokens OR-joined as quoted prefix terms
  (`"stor"* OR ...`) so partial words still hit; `bm25()` returns
  negative-better values, inverted to positive in the engine.
- chunk_ids encode `path::line`; the search JOINs `chunk_hashes` to recover
  line numbers for the hit display.
- Fallback: if the committed index is missing/stale, the engine rebuilds a
  transient BM25 index in memory and prints a `doc-index.py sync` hint —
  search never hard-fails.
- Chunks are heading-aware markdown sections (~1200 chars), so hits name a
  file + line, not just a file. `--top N` (default 6) and max 2 chunks/file
  keep the hit list readable.

## Probe-authoring notes (test_doc_impact.py)

- Expectation values are compared as strings; a trailing `*` means
  startswith (e.g. `vg_k8s_nvme.*` matches the literal live value).
- `ready` is a special dotted key resolving the Node `Ready` condition.
- kubectl must run as `sudo KUBECONFIG=/etc/rancher/rke2/rke2.yaml kubectl ...`
  (env-preserving `sudo -E` is rejected in non-tty contexts).
