---
phase: 05-gitops-bootstrap/02-29-1-appprojects
---
# AppProjects (29.1)

Created three AppProjects in `infra/kubernetes/bootstrap/argocd/projects.yaml`:

- **`platform`** — cluster-wide resources (namespaces `*`, kinds `*`).
- **`tenant-jya0`** — constrained to `dev-jya0`, `prod-jya0`, `ml-jya0`,
  `gpu-jya0`.
- **`tenant-42wasd-admin`** — constrained to `dev-42admin`, `prod-42admin`,
  `games-42admin`.

Both tenant projects allow only the single infra repo as a source, and only
themselves as destinations. This is a second boundary alongside Kubernetes RBAC.

Applied:

```bash
kubectl apply -f infra/kubernetes/bootstrap/argocd/projects.yaml
# appproject.argoproj.io/platform created
# appproject.argoproj.io/tenant-jya0 created
# appproject.argoproj.io/tenant-42wasd-admin created
```

Note: the AppProject `destinations` field uses the singular `namespace` key
(not `namespaces`), which strict decoding rejects.