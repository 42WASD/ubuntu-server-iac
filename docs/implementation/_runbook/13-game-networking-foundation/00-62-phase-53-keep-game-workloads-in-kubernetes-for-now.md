---
phase: 13-game-networking-foundation/00-62-phase-53-keep-game-workloads-in-kubernetes-for-now
---
# Phase 53 — keep game workloads in Kubernetes for now

**Intent:** keep game hosting inside the same infrastructure discipline as the
rest of the platform. Do not solve individual game stacks yet. The two game
lanes get the full governance treatment now, so later we can pick per-game
`StatefulSet` / `Agones` / operator / proxy / controller without touching the
host platform.

## 53.1 The two game lanes

The namespace baseline (Part V) already created both namespaces under
`infra/kubernetes/platform/namespaces/tenants.yaml`:

```text
prd-games-42wasd-admin   canonical production lane (deep-copy source)
dev-games-42wasd-admin   ephemeral, on-demand staging lane (throwaway)
```

`dev-games-42wasd-admin` holds at most one deep-copied game server at a time,
is not a source of truth, and is excluded from canonical backups.

## 53.2 Governance already applied (Part V, verified live)

Each game lane already gets, via GitOps + Argo CD (Part 5):

```text
ResourceQuota   infra/kubernetes/platform/quotas/games.yaml
LimitRange      infra/kubernetes/platform/limitranges/games.yaml
NetworkPolicy   infra/kubernetes/platform/networkpolicies/games.yaml
RBAC            infra/kubernetes/platform/rbac/games.yaml
Namespace       infra/kubernetes/platform/namespaces/tenants.yaml
```

Verified against the cluster:

```bash
kubectl -n prd-games-42wasd-admin get resourcequota,limitrange,networkpolicy
kubectl -n dev-games-42wasd-admin get resourcequota,limitrange,networkpolicy
```

Both lanes show:

```text
resourcequota/namespace-budget     present
limitrange/container-defaults      present
networkpolicy/default-deny         present (Ingress+Egress)
networkpolicy/allow-cluster-dns    present (UDP/TCP 53)
```

Quota ceilings (prd canonical): `requests.cpu: 4`, `limits.cpu: 8`,
`requests.memory: 8Gi`, `limits.memory: 16Gi`, `requests.storage: 200Gi`,
`pods: 30`. Dev staging lane is intentionally smaller
(`requests.cpu: 2`, `requests.memory: 4Gi`, `requests.storage: 50Gi`).

## 53.3 Persistent storage & monitoring — dependencies on earlier parts

- **Persistent storage** for game worlds: OpenEBS LocalPV LVM is not yet
  installed (Part 7, Phase 31/32 pending). StorageClasses `nvme-fast` /
  `hdd-bulk` are designed in the reference but not yet live. Game world PVCs
  will use those once Part 7 lands.
- **Monitoring**: Prometheus/Grafana stack is Part 8 (pending). Game lane
  visibility will come with it.

Phase 53's scope is the **platform decision + governance objects**, which are
complete and live; the storage/monitoring backing is tracked by its own parts.

## 53.4 Controlled external ports (Phase 54 connection)

`default-deny` currently blocks all external ingress. Per Phase 54 the game
edge is a **separate plane** from Cloudflare web: game TCP/UDP enters via
`UAE VPS -> WireGuard -> alpha game Service`, so controlled external ports
will be exposed explicitly by a NetworkPolicy once a game server actually
lands (Phase 53 explicitly defers "controlled external ports" until a real
game workload exists, so none are opened now).