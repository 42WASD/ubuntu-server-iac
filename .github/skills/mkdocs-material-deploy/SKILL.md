---
name: mkdocs-material-deploy
description: "Initialize, configure, and automate technical documentation with MkDocs and the Material theme, then deploy to GitHub Pages via GitHub Actions. Use when: setting up a docs site, creating mkdocs.yml, writing docs/index.md, adding a GitHub Pages deployment workflow, or organizing documentation into a docs/ folder."
user-invocable: true
---

# MkDocs Material Setup & GitHub Pages Deployment

A standardized workflow for initializing, configuring, and automating technical documentation using **MkDocs**, the **Material for MkDocs** theme, and **GitHub Actions**.

## When to Use
- Initializing a new documentation site in an existing repository.
- Creating `mkdocs.yml`, `docs/index.md`, and documentation subpages.
- Adding a GitHub Actions pipeline to deploy docs to GitHub Pages.
- Reorganizing existing guides (`.md` files) into a `docs/` tree.

## Prerequisites
- A local clone of your existing GitHub repository.
- Python 3.10+ installed.

## Target Directory Structure

```
<repository-root>/
├── .github/
│   └── workflows/
│       └── docs.yml              # CI/CD deployment pipeline
├── docs/
│   ├── assets/
│   │   └── images/
│   ├── guides/
│   │   └── getting-started.md
│   └── index.md                  # Site homepage (required)
├── projects/
│   └── pyproject.toml            # uv-managed dependencies (mkdocs, theme, plugins)
├── .gitignore
└── mkdocs.yml                    # Main MkDocs configuration
```

## Procedure

### Step 1 — Virtual Environment & Dependencies (use `uv`)
This repository uses **uv** with a `pyproject.toml` for dependency management (see `AGENTS.md`). In `projects/pyproject.toml`, include the docs toolchain in the `dependencies` list:

```toml
[project]
name = "ubuntu-server-iac-projects"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.5.0",
    "pymdown-extensions>=10.7.0",
    "mkdocs-minify-plugin>=0.8.0",
]
```

Sync and activate:
```bash
cd projects
uv sync
source .venv/bin/activate
```

### Step 2 — Update `.gitignore`
Append Python and MkDocs build artifacts:
```
# Python & Virtualenv
.venv/
__pycache__/
*.pyc

# MkDocs Local Build Artifacts
site/
.cache/
```

### Step 3 — Create `mkdocs.yml`
Configure the Material theme with light/dark palettes, navigation features, markdown extensions, and plugins. See the provided template for the full configuration. Replace placeholders (`<organization>`, `<repository>`) with the GitHub details.

### Step 4 — Scaffold Docs
- Create `docs/index.md` (homepage) and subpages under `docs/guides/`, `docs/setup/`, etc.
- Organize the `nav` section in `mkdocs.yml` to match your file layout.

### Step 5 — Local Verification
Build or serve using `uv run` from the `projects` folder (so the venv is used), pointing at the root `mkdocs.yml`:
```bash
cd projects
uv run mkdocs serve -f ../mkdocs.yml
# or validate strictly:
uv run mkdocs build --strict -f ../mkdocs.yml
```
Preview at `http://127.0.0.1:8000`. Verify theme switching, tabs, code copy, and search.

### Step 6 — GitHub Actions Pipeline
Create `.github/workflows/docs.yml` using the Actions artifact deployment (build job uploads the `./site` artifact; deploy job uses `actions/deploy-pages@v4`).

### Step 7 — Repository Settings
1. GitHub → **Settings** → **Pages** → **Source: GitHub Actions**.
2. Commit and push:
   ```bash
   git add .
   git commit -m "feat(docs): initialize mkdocs with material theme and github action"
   git push origin main
   ```
3. Site live at `https://<organization>.github.io/<repository>/`.

## Troubleshooting
- **Build fails with `--strict`**: broken relative links or missing nav targets → run `mkdocs build --strict` locally.
- **404 on assets/sub-routes**: `site_url` mismatch → ensure `site_url` matches exactly (trailing slash).
- **403 in GitHub Action**: missing token perms → add `pages: write` and `id-token: write`.
- **Mermaid not rendering**: ensure `pymdownx.superfences` has the `mermaid` custom fence configured.