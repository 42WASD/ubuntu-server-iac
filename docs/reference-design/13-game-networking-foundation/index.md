# Game networking foundation

---

## Contents

- [keep game workloads in Kubernetes for now](keep-game-workloads-in-kubernetes-for-now/index.md)
- [why game edge is separate from Cloudflare web](why-game-edge-is-separate-from-cloudflare-web/index.md)
- [relay bring-up](relay-bring-up/index.md)
- [game server orchestration: operator, not raw manifests](game-server-orchestration-operator/index.md)

---

## Related repositories

This part holds the platform-level game *networking foundation* (edge, relay,
performance, orchestration policy). The concrete, canonical game-server
implementation lives in its own repo and consumes this platform:

- **Minecraft network** — [`42WASD/42wasd-mc`](https://github.com/42WASD/42wasd-mc)
  (Velocity proxy, Paper backends, Nakama, CockroachDB, dynamic worlds). Built
  on the RKE2/GitOps platform owned by this repo; its `infra/` carries only the
  game-layer workloads.

Future games (e.g. CS2) follow the same pattern as their own sibling repos.
