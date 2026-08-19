# Agent Instructions

## Python Environment

- **Always use `uv` to create Python virtual environments.**
  - Create: `uv venv`
  - Activate: `source .venv/bin/activate`
  - Install deps: `uv pip install -r <requirements-file>.txt`
  - Do **not** use `python3 -m venv` or `pip` directly.
- When a task involves Python, prefer `uv` for dependency management and venv creation.