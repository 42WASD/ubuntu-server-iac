---
phase: 05-gitops-bootstrap/06-33-phase-24-limitrange
---
# Phase 24 — LimitRange

Added a `container-defaults` LimitRange to every tenant namespace so that a
container with `resources: {}` is not silently unbounded. The LimitRange
supplies sensible `defaultRequest` / `default` / `max` per container that fit
inside each namespace's `namespace-budget` ResourceQuota ceiling.

## 24.1 Manifests

`infra/kubernetes/platform/limitranges/`:

- `jya0.yaml` — `dev-jya0`, `prd-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin`, `prd-42wasd-admin`
- `mlops.yaml` — `mlops` (higher defaults; GPU-backed serving)
- `games.yaml` — `prd-games-42wasd-admin` (canonical) and
  `dev-games-42wasd-admin` (ephemeral staging, intentionally small)

Per-container shape (varies by namespace):

```yaml
defaultRequest: cpu 250m / memory 256Mi / eph 512Mi
default:        cpu 1    / memory 1Gi  / eph 2Gi
max:            cpu 4    / memory 8Gi  / eph 20Gi
```

`prd-jya0` example (verified on cluster):

```json
defaultRequest: {"cpu":"500m","memory":"512Mi","ephemeral-storage":"1Gi"}
default:        {"cpu":"2","memory":"2Gi","ephemeral-storage":"4Gi"}
max:            {"cpu":"8","memory":"16Gi","ephemeral-storage":"30Gi"}
```

Managed by a new Argo child app `platform-limitranges` (sync-wave `-10`) in
`infra/kubernetes/bootstrap/argocd/apps/platform-limitranges.yaml`. The
`platform-root` app auto-discovered it after a hard refresh.

## 24.2 Applied via Argo CD

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-limitranges  Synced  Healthy
```

Verified a `container-defaults` LimitRange in every tenant namespace:

```bash
for ns in dev-jya0 prd-jya0 dev-42wasd-admin prd-42wasd-admin mlops \
          dev-games-42wasd-admin prd-games-42wasd-admin; do
  kubectl -n $ns get limitrange container-defaults --no-headers
done
```

Together with Phase 23's quota, a container that omits resource limits is
now given a bounded default instead of unbounded consumption.