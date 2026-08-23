---
phase: 05-gitops-bootstrap/rbac
---

# Phase 26 — RBAC

Added namespace-scoped Roles and RoleBindings so tenant groups can work in
their own namespaces, with dev namespaces allowing writes and prod (and
`mlops`) read-only — application writes in prod come from Argo CD, not from
developer credentials.

## 26.1 Manifests

`infra/kubernetes/platform/rbac/`:

- `jya0.yaml` — `dev-jya0` (writer), `prd-jya0` (reader) for group `tenant-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin` (writer),
  `prd-42wasd-admin` (reader), `mlops` (reader) for group `tenant-42wasd-admin`
- `games.yaml` — `dev-games-42wasd-admin` (writer),
  `prd-games-42wasd-admin` (reader) for group `tenant-42wasd-admin`

Roles:

- `tenant-developer` — full CRUD on pods/services/endpoints/configmaps/PVCs,
  deployments/replicasets/statefulsets, jobs/cronjobs, plus exec/portforward.
- `tenant-reader` — `get`/`list`/`watch` on the same resource set.

Prod is read-only on purpose: a principal that can create arbitrary prod
Pods can mount Secrets from that namespace even if RBAC denies direct
`get secret`, so writes are confined to Argo CD.

Managed by a new Argo child app `platform-rbac` (sync-wave `-5`) in
`infra/kubernetes/bootstrap/argocd/apps/platform-rbac.yaml`.

## 26.2 Applied via Argo CD

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-rbac  Synced  Healthy
```

Verified every tenant namespace has the expected Role + RoleBinding.

## 26.3 Verified with `kubectl auth can-i`

```bash
kubectl auth can-i create deployments -n dev-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # yes
kubectl auth can-i create deployments -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
kubectl auth can-i get pods -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # yes
kubectl auth can-i get secrets -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
```

Dev group gets writes; prod/`mlops` get read-only and no secret access.
Authentication (Phase 27) is handled separately via OIDC later; this phase is
authorization only.