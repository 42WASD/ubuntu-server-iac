# SSOT Docs Verification Toolkit — Technique & Usage

A complete, deterministic validation pipeline for MkDocs sites built on a
Single-Source-of-Truth (SSOT) manifest. It turns the bugs that used to be found
by manually re-reading files into **automated failures** that run every commit.

## The problem it solves

The `ubuntu-server-iac` docs are driven by a SSOT manifest
(`docs/reference-design/_sequence.yaml`) that generators read to derive all
numbers. Without guardrails, this system fails *silently*:

| Failure mode | Old detection | New detection |
|---|---|---|
| Two `_runbook` files share a `phase:` key → dict silently drops one | manual read | **fails at load** |
| Generator output drifts from committed files | manual diff | **golden test** |
| Broken/missing link or anchor | manual check | **mkdocs `--strict`** |
| Orphaned page (not in nav) | manual scan | **mkdocs `--strict`** |
| Duplicate slug / missing page / phase gap | manual scan | **manifest validation** |
| Stale `progress.yaml` key after rename | manual check | **test** |
| Number-prefixed H1 fighting the SSOT | manual grep | **test** |

## One command

Everything runs from a single entry point:

```bash
bash scripts/docs/verify.sh          # full: validate -> tests -> strict build
bash scripts/docs/verify.sh --stage  # skip the mkdocs build (fast feedback)
```

This is what CI runs, so **local = CI**: same command, same exit code,
everywhere.

## The layers

| Layer | Command / file | Catches |
|---|---|---|
| 1–2 | `scripts/docs/docs_manifest.py --repo .` | structural + runbook invariants |
| 3 | `uv run pytest` (in `projects/`) | golden + parity + lint |
| 4 | `uv run mkdocs build --strict` | links / anchors / orphans |

---

### Layer 1 — fail loudly on silent overwrites

`scripts/docs/docs_manifest.py` gains a `validate_runbooks()` that scans every
`docs/implementation/_runbook/**/*.md` frontmatter for duplicate `phase:` keys
and **exits non-zero** listing the offending files. This makes the "dict
silently drops a runbook" bug impossible to ship.

### Layer 2 — structural manifest validation

`python3 scripts/docs/docs_manifest.py --repo .` checks:

- **Duplicate slugs** within a part's nav subtree (cross-part reuse, e.g. a
  glossary reusing a section name, is allowed).
- **Missing `index.md`** for every part/section/sub-section listed in the
  manifest.
- **Tracked parts have ≥1 section.**
- **Phase continuity** — after `assign_phase_numbers`, tracked sections must be
  `0..N` with no gaps (catches the historical 69/70 collision).

### Layer 3 — golden + parity tests (`projects/tests/`)

| Test file | Covers |
|---|---|
| `test_manifest_invariants.py` | structural validation, no number-prefixed H1s, no stale progress keys, phase continuity |
| `test_golden.py` | **generators are idempotent** (re-running produces zero git diff), rendered page lists every tracked phase |

Run with `cd projects && uv run pytest`.

### Layer 4 — MkDocs native strict validation

`mkdocs.yml` now has a `validation:` block (nav/links/anchors all `warn`), so
`mkdocs build --strict` fails on the first broken link, missing anchor, or
nav-omitted file — no custom code needed.

---

## File layout

```
scripts/docs/
├── docs_manifest.py            # loader + validation (Layer 1-2)
├── docs-generate-nav.py        # nav generator (SSOT-driven)
├── docs-generate-implementation.py
├── verify.sh                   # one-command pipeline
└── README.md                   # this guide
projects/tests/
  ├── conftest.py               # adds scripts/docs to path, fixtures
  ├── test_manifest_invariants.py
  └── test_golden.py
mkdocs.yml                      # validation block (Layer 4)
.github/workflows/docs.yml      # runs verify.sh before building
```

## Using the golden test (Layer 3)

The golden test asserts generators are **idempotent**: running them must not
change committed `mkdocs.yml` / `docs/implementation/index.md`. So:

1. Edit the manifest (`_sequence.yaml`) or a generator.
2. Re-run the generators to regenerate committed output.
3. `git add` the regenerated files together with the source change.
4. CI (and `verify.sh`) proves no drift.

If a test fails with "GENERATED FILES DRIFTED", the committed generated output
does not match what the generators produce — re-run the generators and commit
the result.

## Adding a new validation check

1. Prefer the existing `validate()` in `docs_manifest.py` if it is a structural
   invariant (slug/phase/file) — it runs everywhere (CLI, tests, verify.sh).
2. Otherwise add a `test_*` in `projects/tests/`. It is deterministic, fast,
   and runs in CI automatically.
3. For link/anchor/orphan concerns, tune the `validation:` block instead of
   writing Python.