# Projects

Python-based tooling and documentation environment for `ubuntu-server-iac`.

This folder uses **uv** with a `pyproject.toml` for dependency management. Run `uv sync` to install everything from the lockfile.

## Usage

```bash
cd projects
uv sync
source .venv/bin/activate
```

Then run MkDocs from the repo root:

```bash
cd ..
mkdocs serve
```

## Contents

- `pyproject.toml` — project metadata and dependencies (mkdocs, material theme, dev tools).
- `README.md` — this file.

## Dependency Groups

- **default**: MkDocs + Material theme + minify plugin (docs toolchain).
- **dev**: `pytest`, `ruff` (linting & testing).