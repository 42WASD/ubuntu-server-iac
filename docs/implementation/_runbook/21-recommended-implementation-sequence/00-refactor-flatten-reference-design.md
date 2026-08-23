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

---

## Follow-up: restore "actionable parts only" on the Implementation page

The flatten refactor made `docs-generate-implementation.py` scan all of
`docs/reference-design/`, which wrongly dragged pure conceptual/reference parts
(01, 02, 18–25) onto the Implementation progress page as "phases to complete"
(62/172 = 36% — diluted by non-actionable docs).

**Fix:** added a `tracked: true` frontmatter flag to the 15 actionable parts
(03–17, the former `build/` group) and made the generator's `scan_reference()`
return only `tracked()` parts.

**Commands run:**
```bash
# Add tracked:true to parts 03-17 (sed, one per part index.md)
python3 scripts/docs/docs-generate-implementation.py
cd projects && uv run mkdocs build --strict -f ../mkdocs.yml
```

**Verified:** generator now reports `15 parts, 71 sections`; the page lists only
Parts III–XVII and the summary reads a truthful **62 / 94 (66%)** complete;
`mkdocs build --strict` passes with no warnings.