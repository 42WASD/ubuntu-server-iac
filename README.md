# ubuntu-server-iac

ubuntu-server-iac documentation built on the **Single-Source-of-Truth (SSOT)**
reading-order manifest, guarded by a deterministic verification toolkit that
runs in CI.

This project was generated from [`42WASD/template-docs-project`](https://github.com/42WASD/template-docs-project).
See `.copier-answers.yml` for the exact template commit it was created from.

## Quick start

```bash
# 1. Install deps
cd projects && uv sync

# 2. Run the one-command toolkit (validate -> tests -> strict build)
bash scripts/docs/verify.sh

# 3. Build the site
cd projects && uv run mkdocs build --strict -f ../mkdocs.yml
```

`scripts/docs/verify.sh` is the same command CI runs, so **local = CI**.

## Updating from the template

```bash
copier update .      # 3-way merge in the latest template changes
```

Reads `.copier-answers.yml` (records which template commit you're on), then
merges in improvements without overwriting your own edits.

## The SSOT manifest

`docs/reference-design/_sequence.yaml` is the single source of truth. All
numerals (I, II, III…) and phase numbers (1, 2, 3…) are **derived from list
position** — never stored in page files. To insert/remove/reorder, edit that
one file and re-run `bash scripts/docs/verify.sh`.

## Layout

```
mkdocs.yml                      # config + validation block
docs/
  index.md
  reference-design/
    _sequence.yaml              # SSOT manifest
    <part>/<section>/index.md   # content pages
  implementation/
    progress.yaml               # status per phase
    index.md                    # generated progress page
scripts/docs/
  docs_manifest.py              # loader + structural validation
  docs-generate-nav.py          # nav generator
  docs-generate-implementation.py
  verify.sh                     # one-command pipeline
  README.md                     # the technique guide
projects/
  pyproject.toml                # uv + pytest
  tests/                        # golden + parity tests
.github/workflows/              # CI: verify + deploy pages
```

## Read the technique

`scripts/docs/README.md` — the full technique, the 4 verification layers, and
how to add new checks.