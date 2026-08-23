---
order: 40
---

# Phase 40 — local developer work on alpha

Example:

```bash
ssh jya0@alpha

cd ~/projects/my-api

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements-dev.txt
pytest
```

For Node:

```bash
corepack enable
pnpm install
pnpm test
```

OS/runtime dependencies belong in the container image.

If a project needs:

```text
ffmpeg
libpq
ImageMagick
CUDA userspace
compiler packages
```

do not give the developer sudo.

Put those in the Dockerfile/Containerfile or an approved host development package set.

---
