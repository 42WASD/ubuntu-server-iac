# Phase 69 — game server orchestration: operator, not raw manifests

**Intent:** settle the *how* of managing many game-server instances in
Kubernetes. Phase 53 deferred the per-game choice ("plain StatefulSet / Agones /
operator / proxy layer / specialized controller"). This phase resolves that
choice with researched, current answers: **use a game-native operator per game
(e.g. Shulker for Minecraft), deliver it through Argo CD, and reserve Agones
for ephemeral/match-based game modes.**

---

## 1. The question this phase answers

> Is there a Kubernetes-native operator to manage/configure game servers, or is
> it just Argo CD where we hand-write a manifest for every world?

**Answer: there is a game-native operator, and Argo's job is only to deliver it
(and its declarative config).** You do not hand-write a full StatefulSet for
every world. A per-game operator adds the domain knowledge that raw Kubernetes
workloads lack.

Three layers exist and are complementary:

```text
Argo CD (outer GitOps)  ->  game operator (inner controller)  ->  Pods/State
   "apply the desired     "manage worlds/proxies the way       (the actual
    state from Git"         the game actually works"             servers)
```

---

## 2. The candidate landscape (what "game orchestration" actually means)

| Layer | Tool | What it does | Is it the answer? |
|---|---|---|---|
| GitOps delivery | **Argo CD** | Syncs manifests from Git. **No game knowledge.** | Needed, but not the manager |
| Game-agnostic orchestration | **Agones** (Google+Ubisoft) | `GameServer`/`Fleet` CRDs, allocation API, autoscaling. Built for **session/match-based, ephemeral** servers. | Yes, **for match games** |
| Game-agnostic K8s workload | **OpenKruiseGame** | Hot/in-place update, stateful sets with game awareness | Alternative to Agones |
| **Minecraft-native operator** | **Shulker** | CRDs for **Minecraft servers + proxies**; world-aware lifecycle, save/shutdown | **Yes, for Minecraft** |
| Generic game-server operator | **gameserver-operator** (LinuxGSM) | Declarative game servers via LinuxGSM | Alternative |
| Container image + chart | **itzg/minecraft-server** | One server via env vars; great for a single server | Not multi-world/proxy aware |

### Agones is game-agnostic but assumes *ephemeral* servers
Research is consistent: Agones (and OpenKruiseGame) are built for **matches** —
a server lives minutes–hours, state lives in memory, and it scales in/out and
is torn down. That is the *wrong* model for a **persistent Minecraft world** on a
PVC that you want to keep. So Agones is the right engine for *ephemeral game
modes* (a temporary PvP arena), but not for your permanent worlds.

---

## 3. Decision: game-native operator through Argo

For this platform, adopt the **operator** option from Phase 53's list, layered
under Argo:

- **Argo CD** deploys and upgrades the operator itself (single GitOps app), and
  applies the operator's **Custom Resources** from `infra/kubernetes/games/`.
- **The game operator** (e.g. Shulker for Minecraft) owns the world/proxy
  lifecycle: state-save-before-shutdown, world config, proxy registration,
  rollouts — the domain knowledge Argo neither has nor should have.

This keeps the platform game-agnostic: Argo and the host discipline don't care
which game; the operator carries the game's semantics. Future games just get
their own operator delivered the same way.

---

## 4. Minecraft + Velocity, concretely

The user's Minecraft setup is **persistent worlds + a Velocity proxy network**
— exactly Shulker's target scenario ("servers and proxies").

```text
                    ┌──────────────────────────────────────────────┐
  players ── TCP ──►  Velocity proxy  (Shulker proxy CR)          │
                    │   the one external game port                │
                    └──────────────────┬──────────────────────────┘
                ┌───────────────┬──────┴────────┬──────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌────────────┐  ┌────────────┐
        │  Lobby       │ │  Survival  │  │  Minigames │   <- Shulker
        │ MinecraftServer CRs (each backed by a PVC)   │     server CRs
        └──────────────┘ └────────────┘  └────────────┘
```

- **Velocity** is a first-class **proxy** resource managed by the operator
  (Shulker supports proxies as first-class CRs), NOT a hand-rolled Deployment.
  It sits in front of the world servers, players connect only to it.
- **Each persistent world** is a `MinecraftServer` CR with its own persistent
  storage (OpenEBS PVC), so worlds keep living across restarts.
- **Agones `Fleet`/autoscaling is NOT used for persistent worlds** — it's
  reserved for optional ephemeral match modes later.

### Does the proxy sit "behind the master orchestrator"?
Not behind — **alongside/in front at the game layer, but under Argo's umbrella.**
Argo is the top orchestrator (manages the operator + all CRs). Inside the game
layer, Velocity fronts the worlds. "Behind" a proxy would mean chaining
proxies, which Velocity explicitly does **not** support — one proxy, then the
servers.

---

## 5. Decision for this platform

| Use case | Technology | Why |
|---|---|---|
| Persistent Minecraft worlds + Velocity | **Shulker operator** via Argo | Worlds are stateful/long-lived; operator owns save/lifecycle; proxy is first-class |
| Ephemeral / match-based modes (any game) | **Agones** via Argo | Correct session-lifecycle model; scale up/down |
| Everything delivered | **Argo CD** | GitOps, reproducible, matches platform's existing GitOps pattern |
| Single throwaway server (optional) | itzg Helm chart | Simple; not for multi-world/proxy nets |

Do **not** hand-write a `StatefulSet` per world when a per-game operator already
encodes that. Reserve raw manifests for cases with no operator.

---

## 6. References (researched 2026-08)

- Shulker — "A Kubernetes operator for managing complex and dynamic Minecraft
  infrastructures, including game servers and proxies"
  `github.com/jeremylvln/Shulker` (uses `itzg/docker-minecraft-server`
  and `docker-bungeecord` under the hood)
- Agones — "Host, Run and Scale dedicated game servers on Kubernetes"
  (Google + Ubisoft; `GameServer`/`Fleet` CRDs, allocation API)
- OpenKruiseGame — CNCF game workload (hot/in-place update, stateful)
- gameserver-operator (LinuxGSM) — declarative game servers
- Google "Enterprise Grade Minecraft on Kubernetes" (Casey West): state lives
  on disk → treat as stateful; use a chart (itzg) and backup tooling.

> Note: names/versions verified via web search on the date above; verify the
> operator's maintenance status and CRD shape before adopting.