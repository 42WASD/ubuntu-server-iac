# game server orchestration: operator, not raw manifests

**Intent:** settle the *how* of managing many game-server instances in
Kubernetes. Phase 53 deferred the per-game choice ("plain StatefulSet / Agones /
operator / proxy layer / specialized controller"). This phase resolves that
choice with researched, current answers: **use a per-game controller, deliver it
through Argo CD, and reserve Agones for ephemeral/match-based game modes.** The
platform stays game-agnostic: each game's specific operator choice lives in that
game's own repo.

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
| Per-game controller | **game-specific controller** | Owns the world/lifecycle semantics the game mode needs | Chosen per game, in that game's repo |
| Generic game-server operator | **gameserver-operator** (LinuxGSM) | Declarative game servers via LinuxGSM | Alternative |

### Agones is game-agnostic but assumes *ephemeral* servers
Research is consistent: Agones (and OpenKruiseGame) are built for **matches** —
a server lives minutes–hours, state lives in memory, and it scales in/out and
is torn down. That is the *wrong* model for a **persistent world** on a PVC that
you want to keep. So Agones is the right engine for *ephemeral game modes* (a
temporary PvP arena), but not for permanent worlds.

---

## 3. Decision: per-game controller through Argo

For this platform, adopt a per-game **controller** option from Phase 53's list,
layered under Argo:

- **Argo CD** deploys and upgrades the controller itself (single GitOps app), and
  applies its **Custom Resources / declarative config** from
  `infra/kubernetes/games/`.
- **The per-game controller** owns the world/proxy lifecycle: state-save-before-
  shutdown, world config, proxy registration, rollouts — the domain knowledge
  Argo neither has nor should have.

This keeps the platform game-agnostic: Argo and the host discipline don't care
which game; the controller carries the game's semantics. Future games just get
their own controller delivered the same way. **The concrete controller for each
game is owned and chosen in that game's own repo** (see §6).

---

## 4. Concrete per-game setups live in the game's repo

The platform deliberately does **not** hardcode any one game's orchestration
detail here. A persistent-world + proxy network (whatever the game) is
architected the same generic way, and its concrete realization is documented
in the game's sibling repo:

```text
players -- TCP --> game proxy (the one external game port)
                         |
            +------------+------------+
            v            v            v
        world A       world B      world C   <- per-world controllers/State
   (persistent PVC) (persistent)  (persistent)
```

- **The proxy** is the single external game port; players connect only to it.
- **Each persistent world** keeps its own persistent storage, so worlds survive
  restarts.
- **Agones `Fleet`/autoscaling is NOT used for persistent worlds** — it is
  reserved for optional ephemeral match modes later.

The exact controller, proxy, and per-world representation are decided in the
game's repo (for the concrete Minecraft network, see §6).

---

## 5. Decision for this platform

| Use case | Technology | Why |
|---|---|---|
| Persistent worlds | **Per-game controller** via Argo (chosen in the game's repo) | Worlds are stateful/long-lived; controller owns save/lifecycle |
| Ephemeral / match-based modes (any game) | **Agones** via Argo | Correct session-lifecycle model; scale up/down |
| Everything delivered | **Argo CD** | GitOps, reproducible, matches platform's existing GitOps pattern |

Do **not** hand-write a raw `StatefulSet` per world when a per-game controller
already encodes that. Reserve raw manifests for cases with no controller.

---

## 6. Canonical implementation

The concrete realization of this phase's policy for the Minecraft network — the
per-game controller and proxy chosen for persistent worlds — lives in the
sibling repo
[**`42WASD/42wasd-mc`**](https://github.com/42WASD/42wasd-mc), the game-layer
source of truth. That repo owns its controller/lifecycle decision (its "World
Controller" and StatefulSet+PVC model), which may legitimately differ from an
off-the-shelf operator if the project chose to build its own. This page only
sets platform-level policy.

Future games (e.g. CS2) get their own sibling repo following the same seam.

---

## 7. References (researched 2026-08)

- Agones — "Host, Run and Scale dedicated game servers on Kubernetes"
  (Google + Ubisoft; `GameServer`/`Fleet` CRDs, allocation API)
- OpenKruiseGame — CNCF game workload (hot/in-place update, stateful)
- gameserver-operator (LinuxGSM) — declarative game servers
- Google "Enterprise Game Servers on Kubernetes" (Casey West): state lives on
  disk → treat as stateful; use a chart and backup tooling.

> Note: names/versions verified via web search on the date above; verify the
> controller's maintenance status and CRD shape before adopting. Per-game
> controller choice (e.g. an off-the-shelf operator vs a custom controller) is
> decided in each game's sibling repo, not here.