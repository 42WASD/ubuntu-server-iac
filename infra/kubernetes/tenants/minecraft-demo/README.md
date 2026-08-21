# Minecraft demo — dev-games-42wasd-admin

Demo vanilla Minecraft server deployed to the `dev-games-42wasd-admin`
namespace via Argo CD (project `tenant-42wasd-admin`).

## Components

- `pvc.yaml` — 5Gi world volume on `nvme-fast`.
- `deployment.yaml` — single-replica `itzg/minecraft-server:latest`, cracked
  (`ONLINE_MODE=FALSE`), 2G heap, restricted-PSA compliant (non-root UID/GID
  1000 + `fsGroup: 1000` + drop ALL caps + seccomp RuntimeDefault).
- `service.yaml` — ClusterIP on 25565 (game edge is the UAE relay -> WireGuard,
  reference Phase 54; avoids NodePort/LoadBalancer which Kyverno flags).
- `networkpolicy.yaml` — allows ingress on 25565 and outbound internet (the
  image downloads the vanilla jar on first start).

## Why one replica + Recreate

Vanilla Minecraft is a single in-memory process that owns the world files on
the PVC. Two pods would both try to open the same level and corrupt it. We pin
`replicas: 1` and use `strategy: Recreate` so a rolling replacement never runs
two writers at once.

## Reach it (dev)

```bash
kubectl port-forward -n dev-games-42wasd-admin svc/minecraft-demo 25565:25565
```

Then connect a (cracked) client to `localhost:25565`. Later the game edge
(UAE relay -> WireGuard -> ClusterIP) can front this Service.

## Security notes

- `ONLINE_MODE=FALSE` means any (offline/cracked) client can join — dev only.
- The namespace is restricted PSA + default-deny network policy.
- Egress to the whole internet is allowed so the server can fetch the vanilla
  jar and hit Mojang endpoints. Tighten to an allow-list of Mojang IPs before
  any production deployment.