# Relocate Minecraft-specific knowledge to `42wasd-mc`

**Intent:** clear separation of concerns. The platform repo (`ubuntu-server-iac`)
should hold generic, game-agnostic game-networking policy; Minecraft-specific
details (Shulker, Velocity, Paper tuning, itzg images, MSPT) belong in the
Minecraft project repo `42WASD/42wasd-mc`.

**What changed (iac):**
1. **Removed `minecraft-server-performance` (was Phase 56)** — ~100% Minecraft-
   specific (MSPT, 20 TPS, Paper/Spigot config, Spark, Aikar flags). Relocated
   into `42wasd-mc/docs/reference-design/04-technical-reference/performance-
   principles/`. Deleted from iac; SSOT renumbering made `game-server-
   orchestration-operator` Phase 56 (was 57).
2. **`game-server-orchestration-operator` made game-agnostic** — removed the
   Shulker hardcoding and the Minecraft+Velocity concrete diagram. Now states
   platform policy (per-game controller through Argo; Agones for ephemeral) and
   defers the concrete controller choice to each game's sibling repo.
3. **`why-game-edge-is-separate-from-cloudflare-web`** — the Velocity player-info
   forwarding block was replaced with a generic "game-aware proxy" rule; the
   concrete Velocity config is documented in `42wasd-mc`.
4. **`relay-bring-up`** — fixed the "Minecraft proxy (Velocity)" cross-reference
   to a generic "game-aware proxy" + pointer to sibling repo.

**What changed (42wasd-mc):**
- `04-technical-reference/performance-principles/index.md` — now the canonical
  Minecraft-performance reference (absorbed the relocated MSPT/Paper/GC tuning
  content), with a note that it was relocated from the platform.

**Commands run:**
```bash
# iac: remove the MC-specific page + its SSOT/progress entries
git rm -r docs/reference-design/13-game-networking-foundation/minecraft-server-performance
# (edit _sequence.yaml, progress.yaml, part index.md, orchestration/edge/relay pages)

# iac: regenerate nav + implementation from SSOT (renumbers downstream phases)
python3 scripts/docs/docs-generate-nav.py
python3 scripts/docs/docs-generate-implementation.py

# build both
cd projects && uv run mkdocs build --strict -f ../mkdocs.yml   # iac
# 42wasd-mc: edited performance-principles, regenerated nav, built
cd 42wasd-mc && python3 scripts/docs/docs-generate-nav.py
cd 42wasd-mc/projects && uv run mkdocs build --strict -f ../mkdocs.yml
```

**Verified:**
- Both `uv run mkdocs build --strict` pass.
- iac game section no longer contains Shulker/Velocity-specific duplicated
  content (only cross-references to `42wasd-mc`).
- `42wasd-mc` already owned the concrete decision (custom World Controller +
  StatefulSet + PVC, Shulker rejected), consistent with iac's new deferral.