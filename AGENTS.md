# Agent Instructions

## Elevated Privileges (sudo)

- **Whenever a task requires root/sudo privileges, run the `sudo` command
  directly and then prompt the user to enter the password interactively in the
  terminal.** Do **not** substitute another approach, work around the missing
  privilege, skip the step, or mark it "pending" just because you lack sudo.
- The user will type the password into the terminal prompt themselves (never
  send passwords through chat or the model). You run the privileged command;
  they authenticate.
- Run exactly one `sudo` command at a time, wait for it to complete, then
  continue. If a command needs input (like the sudo password prompt), send it
  to the terminal and let the user authenticate interactively.

## Repository Layout & File Placement (Overarching Rule)

- **Whenever creating or adding any new file, always stop and consider whether
  it belongs in a new subfolder or in an existing, more appropriate location.
  Do not default to the top of a folder.**
- If a new file is one of several related files (e.g. scripts for a domain),
  group them under a dedicated subfolder rather than scattering them.
- When in doubt, check the surrounding repo structure first (e.g. `scripts/`
  already has domain subfolders: `docs/`, `gpu/`, `stress/`, `vpn/`) and place
  the file to match the established convention.

## Python Environment

- **Always use `uv` to manage Python virtual environments and dependencies.**
  - Python projects in this repo live under `projects/` and are managed via `pyproject.toml` + `uv.lock`.
  - Create/activate the venv and install all deps: `uv sync` (run from the `projects/` directory).
  - Run a tool from the venv without activating it: `uv run <command>` (e.g. `uv run mkdocs build`).
  - Activate manually if needed: `source projects/.venv/bin/activate`.
  - Do **not** use `python3 -m venv`, `pip`, or plain `requirements.txt` directly.
- When a task involves Python, prefer `uv` for dependency management and venv creation.
- **MkDocs docs site:** config is at repo root (`mkdocs.yml`), sources in `docs/`. Build/serve from `projects/` using `uv run mkdocs build --strict -f ../mkdocs.yml` (or `uv run mkdocs serve -f ../mkdocs.yml`). The generated `site/` lands at the repo root.

## Verification — MANDATORY before commit

- **Before committing ANY change** to docs, the SSOT manifest
  (`docs/reference-design/_sequence.yaml`), a generator, or `mkdocs.yml`, you
  MUST run the full verification pipeline and it MUST pass:

  ```bash
  bash scripts/docs/verify.sh          # full: validate -> tests -> strict build
  bash scripts/docs/verify.sh --stage  # skip the slow mkdocs build (fast)
  ```

  This is exactly what CI runs, so **local = CI**. A change is not "done" until
  `verify.sh` reports **`VERIFY OK`**. Never commit, open a PR, or push if the
  pipeline fails or was skipped.
- The **golden test** asserts generators are idempotent: it fails if committed
  generated output (`mkdocs.yml` nav, `docs/implementation/index.md`) doesn't
  match what the generators produce. When you edit the manifest or a generator,
  regenerate and **commit the regenerated output together** with the change.

## Runbook — record every command you run

- **Whenever you run commands to implement, configure, verify, or change the
  infrastructure, you MUST record them in the runbook immediately** — same
  turn as the work, not later. This is a hard rule, not a nice-to-have.
- **Where:** `docs/implementation/_runbook/<part>/phase-<NN>-<slug>.md`
  (one file per phase; pick the closest existing phase file or create one).
- **What to include:** the exact commands run (verbatim), what they did, and
  what was verified/observed. Use a code block, in the appropriate section.
- **Do not** record transient/exploratory probing or failed attempts unless
  they changed the system or are instructive.
- **After recording, regenerate and rebuild:**
  `python3 scripts/docs/docs-generate-implementation.py` then
  `cd projects && uv run mkdocs build --strict -f ../mkdocs.yml`
- If you complete a phase, also bump its status in `docs/implementation/progress.yaml`.
- See `/memories/repo/runbook-process.md` for the full workflow.

## Doc-impact — check docs for staleness after live commands

- **After any successful run of new/implementing commands** (anything that
  installed, configured, created, renamed, scaled, or removed something on
  the host or cluster), run a quick doc-impact check **before finishing the
  turn**:

  **Step 1 — smart diff (semantic doc lookup):** describe what changed and
  retrieve the docs that talk about the same things (hybrid BM25 + fuzzy
  matching, so reworded/renamed things still hit):

  ```bash
  cd projects
  uv run python ../scripts/docs/doc-impact/impact_search.py \
    "scaled minecraft-demo to 0, prod velocity now owns nodePort 30079"
  # --json for machine-readable output; --top N for more candidates
  ```

  **Step 2 — load and reconcile:** open each hit, compare its claims against
  what actually changed, and edit whatever is stale. Fix the docs **in the
  same turn**.

  **Step 3 — regression battery (deterministic claims):** run the declarative
  live-state probes, which catch the known-persistent claims without any
  retrieval:

  ```bash
  uv run pytest tests/test_doc_impact.py -q -m quick   # ~2s, host-only claims
  uv run pytest tests/test_doc_impact.py -q            # full probe (cluster+VPS)
  ```

  Expectations live in `scripts/docs/doc-impact/live-expectations.yaml` — one
  declarative entry per documented claim. Failing tests name the docs to fix.
- **If a claim is wrong or a new persistent fact got documented** (new VG, new
  service, new config path): edit `live-expectations.yaml` (add or adjust a
  YAML entry — no code needed), then update the docs and commit both together.
- Full doc-vs-reality sweeps (like the 2026-08-29 audit) should be recorded
  as a runbook entry too, so the reconciliation itself is traceable.