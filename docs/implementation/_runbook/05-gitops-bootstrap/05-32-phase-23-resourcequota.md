---
phase: 05-gitops-bootstrap/resourcequota
---

# Phase 23 — ResourceQuota

Applied a `namespace-budget` ResourceQuota to every tenant namespace as a
**ceiling** (not a reservation). Ceilings may sum beyond physical capacity; the
sum of actually-scheduled requests cannot.

## 23.1 Manifests

`infra/kubernetes/platform/quotas/`:

- `jya0.yaml` — `dev-jya0`, `prd-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin`, `prd-42wasd-admin`
- `mlops.yaml` — `mlops`, includes `requests.nvidia.com/gpu: "1"` ceiling
- `games.yaml` — `prd-games-42wasd-admin` (canonical) and
  `dev-games-42wasd-admin` (ephemeral staging, intentionally small)

Values come from the initial quota reference (`02-110`), with game lanes
documented as "tune after games".

Managed by a new Argo child app `platform-quotas` (sync-wave `-10`) in
`infra/kubernetes/bootstrap/argocd/apps/platform-quotas.yaml`. The
`platform-root` app auto-discovered it after a hard refresh.

## 23.2 Applied via Argo CD

```bash
kubectl -n argocd get applications
# platform-quotas  Synced  Healthy
```

Verified a `namespace-budget` quota in every tenant namespace:

```bash
for ns in dev-jya0 prd-jya0 dev-42wasd-admin prd-42wasd-admin mlops \
          dev-games-42wasd-admin prd-games-42wasd-admin; do
  kubectl -n $ns get resourcequota namespace-budget --no-headers
done
```

`mlops` hard limits include:

```json
{"requests.nvidia.com/gpu":"1","requests.cpu":"8","limits.cpu":"16",
 "requests.memory":"16Gi","limits.memory":"32Gi", ...}
```

The GPU ceiling is defined now; the physical GPU is added in a later phase.
GPU is governed by quota + admission, not namespace splitting.

2026-09-01: `quotas/jya0.yaml` (`dev-jya0`/`prd-jya0` budgets) deleted with
the jya0 tenant — see the phase-21 decommission note.