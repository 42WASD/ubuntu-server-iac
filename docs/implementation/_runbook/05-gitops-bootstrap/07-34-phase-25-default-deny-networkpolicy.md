---
phase: 05-gitops-bootstrap/07-34-phase-25-default-deny-networkpolicy
---
# Phase 25 — default-deny NetworkPolicy

Added a `default-deny` NetworkPolicy (Ingress + Egress) to every tenant
namespace, plus an `allow-cluster-dns` egress rule so workloads can still
resolve CoreDNS. Additional per-application flows are added later as needed.

## 25.1 Manifests

`infra/kubernetes/platform/networkpolicies/`:

- `jya0.yaml` — `dev-jya0`, `prd-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin`, `prd-42wasd-admin`, `mlops`
- `games.yaml` — `prd-games-42wasd-admin` (canonical) and
  `dev-games-42wasd-admin` (ephemeral staging)

Each namespace gets:

```yaml
# default-deny
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]

# allow-cluster-dns
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports: [UDP 53, TCP 53]
```

Enforced by the bundled Cilium CNI (network policy mode on).

Managed by a new Argo child app `platform-networkpolicies` (sync-wave `-5`)
in `infra/kubernetes/bootstrap/argocd/apps/platform-networkpolicies.yaml`.
The `platform-root` app auto-discovered it after a hard refresh.

## 25.2 Applied via Argo CD

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-networkpolicies  Synced  Healthy
```

Verified `default-deny` + `allow-cluster-dns` in every tenant namespace:

```bash
for ns in dev-jya0 prd-jya0 dev-42wasd-admin prd-42wasd-admin mlops \
          dev-games-42wasd-admin prd-games-42wasd-admin; do
  kubectl -n $ns get networkpolicies
done
```

The existing `demo-meme` workload lives in a separate non-tenant namespace
and is unaffected (still Running).