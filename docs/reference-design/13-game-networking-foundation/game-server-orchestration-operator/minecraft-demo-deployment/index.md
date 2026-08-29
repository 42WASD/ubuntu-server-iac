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
| `service.yaml` | **NodePort** 30079 → :25565 (game edge = UAE relay → WireGuard → NodePort) |
| `networkpolicy.yaml` | allow ingress 25565 + outbound internet (jar download) |
| `pvc.yaml` | 5Gi world volume on `nvme-fast` |

Argo Application:
`infra/kubernetes/bootstrap/argocd/apps/tenant-minecraft-demo.yaml`
(project `tenant-42wasd-admin`, destination `dev-games-42wasd-admin`).

## Platform rules this workload demonstrates

- **One replica + `Recreate`**: vanilla is a single in-memory process owning
  the world files — a new pod must never start before the old one is gone.
- **NodePort via game edge**: external players hit the UAE relay VPS
  (`:25565`), which DNATs into the WireGuard tunnel to the NodePort. The
  Kyverno `restrict-exposure-and-image-tags` policy records the NodePort in
  **Audit** mode (does not block).
- **Default-deny egress, with an explicit allow**: the games namespace is
  default-deny; the NetworkPolicy allows outbound internet for the jar
  download plus cluster DNS.
- **Non-root, restricted pod security**: UID/GID 1000, `capabilities.drop:
  [ALL]`, seccomp `RuntimeDefault`, `allowPrivilegeEscalation: false`.

## Concrete Minecraft performance/lifecycle tuning

Owned by `42wasd-mc` (MSPT/TPS targets, Paper config, world-controller
choice). This platform repo deliberately does not duplicate it.
