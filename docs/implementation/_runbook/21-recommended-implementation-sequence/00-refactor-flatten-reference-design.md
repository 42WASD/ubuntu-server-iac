# Docs refactor — flatten reference-design to linear I→XXV + semantic slugs

**Intent:** fix the fragmented reference-design navigation ordering and make the
ordering robust to renumbering, so the build narrative reads as one linear
sequence.

**What changed:**
1. **Flattened the 3 group folders** (`background/`, `build/`, `reference/`)
   into a single `docs/reference-design/<NN-part>/`. Parts now sort I→XXV
   linearly, matching the canonical source — no more group-dir jumps.
2. **Semantic slugs.** Dropped the numeric prefix from every section folder
   (`NN-GG-phase-N-slug` → `slug`).
3. **`order:` frontmatter** on every part/section/sub-section `index.md`.
   Parts=Roman numeral, build phases=phase number, other sections=doc order.
4. **Generators sort by `order`** instead of filename
   (`docs-generate-nav.py`, `docs-generate-implementation.py`).
5. **Migrated keys**: `progress.yaml` and `_runbook` `phase:` frontmatter now
   use `<part>/<slug>`.
6. **Resolved phase collisions**: game `minecraft-server-performance` was `56`
   (collided with backups-etcd) → now `69`; `game-server-orchestration` `69` →
   `70`. Canonical phases 0–68 kept their numbers; result is contiguous 0–70.

**Commands run:**
```bash
# Flatten + rename + inject order frontmatter
python3 scripts/docs/docs-flatten-reference-design.py

# Regenerate nav + implementation
python3 scripts/docs/docs-generate-nav.py
python3 scripts/docs/docs-generate-implementation.py

# Build (strict validates all links)
cd projects
uv run mkdocs build --strict -f ../mkdocs.yml
```

**Verified:** `mkdocs build --strict` passes with no warnings; the implementation
progress page lists all 25 parts in linear I→XXV order.