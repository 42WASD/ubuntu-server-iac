# Agent Instructions

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