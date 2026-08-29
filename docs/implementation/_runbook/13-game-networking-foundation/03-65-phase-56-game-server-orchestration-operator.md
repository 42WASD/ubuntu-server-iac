---
phase: 13-game-networking-foundation/game-server-orchestration-operator
---

# Phase 56 — game server orchestration: operator, not raw manifests

**Decision (platform-level, game-agnostic):** game servers run in Kubernetes
under a **per-game controller delivered by Argo CD**; Agones is reserved for
ephemeral/match-based modes. The concrete controller choice lives in each
game's sibling repo — for Minecraft that is
[`42WASD/42wasd-mc`](https://github.com/42WASD/42wasd-mc) (its World
Controller + StatefulSet/PVC model).

## What the platform owns

- **Namespace & governance for games** (already in place):
  - `infra/kubernetes/platform/networkpolicies/games.yaml` — default-deny +
    explicit allows (game edge ports, cluster DNS, workload egress).
  - `infra/kubernetes/platform/rbac/games.yaml` — `dev-games-42wasd-admin`
    (writer), `prd-games-42wasd-admin` (reader) for `tenant-42wasd-admin`.
  - `infra/kubernetes/platform/quotas/games.yaml` and `limitranges/games.yaml`.
- **Argo delivery**: game workloads land as Argo apps in project
  `tenant-42wasd-admin` (e.g. `tenant-games-alpha.yaml`,
  `tenant-minecraft-demo.yaml`).

## First realization (Minecraft demo)

The first concrete workload under this policy is the Minecraft demo — see the
two subsection runbooks of this phase:

- `minecraft-demo-deployment` (deployment record: Deployment/Service/NetworkPolicy/PVC + Argo app)
- `cilium-stale-node-ip-recovery` (operational recovery record hit while
  bringing the game edge up)

## References

- Research summary (Agones / OpenKruiseGame / gameserver-operator): see the
  reference page §2 and §7 (verified 2026-08).
