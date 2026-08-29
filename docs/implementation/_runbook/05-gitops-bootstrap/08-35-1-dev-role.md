---
phase: 05-gitops-bootstrap/rbac/dev-role
---

# dev Role (26.1)

The `tenant-developer` Role grants full CRUD on pods, services, endpoints,
configmaps, PVCs, deployments/replicasets/statefulsets, jobs/cronjobs, plus
`exec`/`portforward`, scoped to a single dev namespace. The RoleBinding binds
the identity group — subject name `42WASD:tenant-42wasd-admin` (the Dex/OIDC
groups claim is org-prefixed) — into that namespace.

Part of Phase 26 — RBAC, applied via Argo CD (`platform-rbac` app,
sync-wave -5; live 2026-08-29: Synced/Healthy):

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-rbac  Synced  Healthy
```

Verified with impersonation using the exact group subject:

```bash
kubectl auth can-i create deployments -n dev-42wasd-admin \
  --as=devuser --as-group="42WASD:tenant-42wasd-admin"   # yes
```