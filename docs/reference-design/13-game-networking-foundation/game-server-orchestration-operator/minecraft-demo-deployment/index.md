# Minecraft demo deployment

The first concrete game workload on `alpha`, used to prove the Part XIII game
edge end-to-end: relay → WireGuard → NodePort → pod, with GitOps delivery,
PVC-backed world storage, and policy governance. The **game-layer source of
truth stays in [`42WASD/42wasd-mc`](https://github.com/42WASD/42wasd-mc)** —
this page records only the platform-facing deployment shape.

## Manifests

`infra/kubernetes/tenants/minecraft-demo/`:

| File | Purpose |
|---|---|
| `deployment.yaml` | single-replica `Recreate` Deployment, 2G heap |
| `service.yaml` | `ClusterIP` :25565 — **scaled to 0**; the game edge NodePort (30079) moved to the prod `velocity` proxy (see below) |
| `networkpolicy.yaml` | allow ingress 25565 + outbound internet (jar download) |
| `pvc.yaml` | 5Gi world volume on `nvme-fast` |

Argo Application:
`infra/kubernetes/bootstrap/argocd/apps/tenant-minecraft-demo.yaml`
(project `tenant-42wasd-admin`, destination `dev-games-42wasd-admin`).

## Platform rules this workload demonstrates

- **One replica + `Recreate`**: vanilla is a single in-memory process owning
  the world files — a new pod must never start before the old one is gone.
- **NodePort via game edge (now on prod Velocity)**: the demo originally held
  NodePort 30079; the edge is now served by the prod `velocity` proxy in
  `prd-games-42wasd-admin` (`25565:30079`). The UAE relay VPS DNATs public
  `:25565` (and the whole 30000–30199 game range) into the WireGuard tunnel.
  The Kyverno `restrict-exposure-and-image-tags` policy records game-range
  NodePorts in **Audit** mode (does not block).
- **Default-deny egress, with an explicit allow**: the games namespace is
  default-deny; the NetworkPolicy allows outbound internet for the jar
  download plus cluster DNS.
- **Non-root, restricted pod security**: UID/GID 1000, `capabilities.drop:
  [ALL]`, seccomp `RuntimeDefault`, `allowPrivilegeEscalation: false`.

## Concrete Minecraft performance/lifecycle tuning

Owned by `42wasd-mc` (MSPT/TPS targets, Paper config, world-controller
choice). This platform repo deliberately does not duplicate it.
