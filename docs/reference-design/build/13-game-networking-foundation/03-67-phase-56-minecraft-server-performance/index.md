# Phase 56 — Minecraft server performance (MSPT headroom & player scale)

**Intent:** capture the researched, verified path to keep a Paper/modded Minecraft
server at 20 TPS (smooth) with **maximum MSPT headroom** — including handling a
**large number of players** — **without breaking mods/plugins**.

---

## 0. The core model (why "smoother" = lower MSPT, not higher TPS)

- Minecraft's game clock runs at a **fixed 20 TPS** (one tick every 50 ms). 20 TPS
  is the **hard ceiling**; it never exceeds 20 on a healthy server. From the
  Minecraft Wiki: *"the game doesn't speed up when the server has extra capacity —
  TPS maxes out at 20."*
- **MSPT** (milliseconds per tick) is the real measure of headroom:
  - MSPT ≤ ~10–20 → huge headroom, buttery smooth, never dips
  - MSPT 30–50 → near the edge, prone to dips under spikes
  - MSPT > 50 → TPS drops below 20 → visible stutter / rubber-banding
- **Therefore "smoother experience" = reducing MSPT / increasing headroom, not
  raising TPS.** Raising TPS above 20 (`/tick rate N`, Java 1.20.5+) only *speeds
  up the game clock* (faster day/night, faster crops) and desyncs clients — it is
  never a smoothness improvement for a real server.
- **Ping vs TPS are orthogonal.** Player ping is network RTT (mac → VPS → tunnel →
  pod); TPS is server processing speed. A server at 20 TPS can still show a high
  ping for a distant player. Optimizing MSPT does **not** lower ping.

### Reading the health numbers
- `tps` → 20.0 / 20.0 / 20.0 is perfect.
- `mspt` (Paper) → shows avg/max ms per tick; watch the **max** (spikes), not just
  avg.
- `spark healthreport` → automated health check (tick, CPU, disk, GC).
- Target: **MSPT max stays well under 50 ms even at peak**, ideally ≤ ~30.

---

## 1. Layer 1 — Runtime & GC (biggest, most reliable wins)

The **#1 cause of MSPT spikes is GC stop-the-world pauses** freezing the tick
loop. Fixing the JVM is the highest-leverage step.

### JVM flags (Aikar's flags / generator)
Use Aikar's flag generator, not hand-rolled guesses. Core ideas:

```text
-Xms equal to -Xmx            # no heap resizing
-XX:+UseG1GC                  # parallel, region-based GC (default on 17+)
-XX:MaxGCPauseMillis=200      # bound GC pause target
-XX:+ParallelRefProcEnabled   # speed up reference cleanup
-XX:+AlwaysPreTouch           # pre-allocate heap, avoid later stalls
-XX:G1NewSizePercent=30
-XX:G1MaxNewSizePercent=40
-XX:G1HeapRegionSize=8M
-XX:G1ReservePercent=20
-XX:G1MixedGCCountTarget=4
```

- For **very large heaps / many players**, consider **ZGC** (Z Generational) or
  ShenandoahGC — both are *concurrent* (do not stop-the-world for the whole
  pause), trading some CPU/RAM for near-zero GC pauses. Only with ≥6G heap.
- Avoid very old flags (`-XX:+CMSIncrementalMode`, etc.) — they hurt.

### Kubernetes specifics
- `requests.memory` should comfortably exceed `-Xmx` (JVM heap + metaspace +
  thread stacks + off-heap). The itzg image maps `MEMORY` to `-Xmx/-Xms`. If
  `-Xmx=2G`, set pod `limits.memory` ≥ 3–4G to avoid the OOM-killer killing the
  JVM mid-tick (an OOM kill is the ultimate MSPT spike).
- CPU: for a single Minecraft server, **core count barely matters beyond 4**
  (main thread is 1 core). 4 cores cover main thread + netty IO + chunk workers
  + plugin async. More cores help only multiple servers / Folia / heavy parallel
  work.
- In the pod, ensure `nproc` / CPU quota is enough; `limits.cpu` = 2 is a sane
  starting floor for a modded server; `limits.cpu` = 4 is the PaperMC/Spigot
  recommendation for 1.15+.

---

## 2. Layer 2 — Paper/Spigot config (per-tick work reduction)

These reduce *how much the server does each tick*, directly lowering MSPT.
**None change gameplay** meaningfully if kept to safe limits.

### Distances (the biggest single lever)
- **View distance**: 7–10 chunks (players still see far).
- **Simulation distance**: **~4 chunks** — the server only ticks what's near.
  The classic trick: high `view-distance` + low `simulation-distance` → players
  see far but the server simulates little. (Leave `view-distance` "default" in
  `spigot.yml` for 1.18+ and set simulation in `server.properties`/Paper.)
- **mob-spawn-range**: keep ≤ effective simulation distance (4–6 chunks).

### Entities (the other big lever)
- **max-entity-collisions**: 8 → **2** (every entity checks collisions each tick;
  lowering to 2 cuts lots of calculation where mobs/players/item frames are dense).
- **Despawn ranges**: hard 128 → **72** (56 for water mobs) — dramatically fewer
  entities tracked; players rarely notice.
- **Entity tick-rate increases** (villagers to 100–200 etc.) — but do **not** go
  above ~200 or villagers stop pathfinding / break trading.
- **nerf-spawner-mobs: true**, **tick-inactive-villagers: false**.
- Keep total **entity tick time < 30%** of a tick (see Spark).

### Redstone / hoppers
- Use Paper's **alternative redstone algorithm** (big redstone-line wins).
- Increase **hopper-check-interval** / disable `HopperEvent` moves where possible.

### Chunk pre-generation
- **Pre-generate the world** (`/paper` + **Chunky** plugin) — the #1 way to stop
  on-the-fly chunk-gen MSPT spikes when players explore. Huge for modded servers
  (mod chunk-gen is expensive).

### Suggested safe baseline (keeps vanilla gameplay)
```yaml
# server.properties
view-distance=7
simulation-distance=4

# paper-global / paper-world-defaults.yml
mob-spawn-range: 6
```
plus the entity/collision/redstone settings above within tested-safe ranges.

---

## 3. Layer 3 — Performance tooling (paper, plugins)

Best tooling, all **safe, no gameplay change**:

| Tool | Purpose |
|---|---|
| **Spark** | Profiling; `spark tps`, `spark healthreport`, `spark profiler` |
| **Chunky** | Pre-generation |
| **ClearLagg** | Entity/world management, periodic lag relief |
| **VillagerOptimiser** | Cut villager AI cost (trading halls) |
| **FarmLimiter** | Cap entity counts / mob-farm explosions |

If a plugin is expensive (per the runbook: e.g. stacker/living stacked mobs)
**remove it** — a single bad plugin is often 40% of a tick. Forced `Spark` to find
the actual top consumer before tuning blindly.

---

## 4. Layer 4 — Large player counts **while keeping mods/plugins**

If a single 20-TPS tick can't keep up with many players, the options are:

### A. Stay on Paper + plugins (recommended first)
Keep TPS at 20 with headroom via Layers 1–3 (GC, distances, entities, pre-gen).
This is the "use Paper unless you need region threads" consensus. **Zero mod/plugin
compat changes.** Handles ~100 players on optimized settings / good CPU.

### B. Folia (PaperMC) — true region multithreading
Folia splits the world into **independent ticking regions**, each ticked in
parallel on a thread pool — **no main thread**. Spread-out players each get their
own region thread → can reach 300–1000+ players (vs ~150 on Paper).

**The tradeoff — it affects mods/plugins:**
- Only **Folia-compatible plugins** work. **Bukkit/Paper plugins like TabListPing
  break.** Most plugins will need to be rewritten/forks.
- Requires ≥16 cores ideally; world pre-generated; `thread-regions.threads` config.
- **Do not use if you rely on ordinary Bukkit/Paper plugins.** It is a fork that
  does not merge back into Paper.

### C. Fabric/NeoForge optimization mods (server-side, mod-compatible)
For **modded (Fabric/NeoForge) servers**, these lower MSPT with zero gameplay
change, even at high player counts:
- **Lithium** — optimizes game mechanics (single-thread, huge wins, no gameplay
  change).
- **VMP / very many players** — optimizes player tracking, chunk sending, entity
  visibility at high player counts.
- **C2ME** (Concurrent Chunk Management Engine) — parallel chunk gen/IO using
  multiple cores.
- **Server Core** — general server performance.
- **AI Improvements** — cheaper mob pathfinding (heavy modpacks).
- Recommended safe bundle: **"Essentially Optimized (Server)"** — a curated,
  tested Fabric server-side pack (Lithium + VMP + C2ME + Server Core + more),
  ~2× chunk-loading, lower RAM, stable 20 TPS.

### D. Multi-instance / proxy (very large, spread-out)
- **Velocity** (BungeeCord successor) as an L7 proxy to split player load across
  multiple backend servers — also the *verified solution* for preserving player IP
  (see Phase 54/55). Does not change per-server tick; adds a layer that can bundle
  player-facing latency display (proxy-only ping) — relevant to the
  TabListPing/latency work.

---

## 5. Decision guidance

| Scenario | Recommended | Mod/plugin impact |
|---|---|---|
| Dev/small, Paper + TabListPing | **Stay on Paper**, Layers 1–3 | none |
| Modded (Fabric/NeoForge), heavy pack | **C: Lithium + VMP + C2ME** | none (compatible) |
| 100+ spread-out players | **A (tuned) → B Folia if needed** | B breaks non-Folia plugins |
| Many servers / player fan | **Proxy (Velocity)** | add proxy layer |

**Rule of thumb:** raise TPS headroom first with Layers 1–3 (free, no compat
impact). Only adopt Folia / scale-out when a single tuned Paper server can't hold
20 TPS at your player count. The bulk (Paper) is the safe default that keeps
mods/plugins (and TabListPing) working.

---

## 6. Verified current-state note (this repo)

On the live `minecraft-demo` (Paper 26.2, 1 replica, `-Xmx2G`, `limits.cpu:2 /
mem:3G`):
- `tps` = **20.0 / 20.0 / 20.0** (perfect).
- CPU usage ~0.16 cores → huge headroom; **not compute-limited**.
- So MSPT is expected to be very low; the 49/100 ms player ping is **network**, not
  MSPT/TPS (see runbook §6b). Optimization above matters only as the server scales
  to many players/mods.

**Next step:** pull the actual `mspt` (`/mspt` via RCON) to quantify headroom, then
apply Layer 1 (GC/Aikar) + Layer 2 (distances) when the workload justifies it.