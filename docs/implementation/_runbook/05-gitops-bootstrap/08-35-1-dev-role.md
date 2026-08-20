---
phase: 05-gitops-bootstrap/08-35-phase-26-rbac/dev-role
---
# dev Role (26.1)

The `tenant-developer` Role grants full CRUD on pods, services, endpoints,
configmaps, PVCs, deployments/replicasets/statefulsets, jobs/cronjobs, plus
`exec`/`portforward`, scoped to a single dev namespace. The RoleBinding binds
the identity group (e.g. `tenant-42wasd-admin`) into that namespace.

Part of Phase 26 — RBAC, applied via Argo CD:

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-rbac  Synced  Healthy
```

Verified the `dev-42wasd-admin` namespace has the expected Role + RoleBinding.