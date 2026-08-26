---
phase: 05-gitops-bootstrap/root-gitops-application/appprojects
---

# AppProjects (29.1)

Created three AppProjects in `infra/kubernetes/bootstrap/argocd/projects.yaml`:

- **`platform`** — cluster-wide resources (namespaces `*`, kinds `*`).
- **`tenant-jya0`** — constrained to `dev-jya0`, `prd-jya0`.
- **`tenant-42wasd-admin`** — constrained to `dev-42wasd-admin`,
  `prd-42wasd-admin`, `mlops`, `dev-games-42wasd-admin`,
  `prd-games-42wasd-admin`.

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

---

## Follow-on: `tenant-community-web` (public web app in GitOps)

The 42WASD community website (`prd-42wasd-admin`) was previously applied to
the cluster by hand (no `argocd.argoproj.io/` tracking). Wired it into GitOps
so Argo CD owns the Deployment/Service/Ingress/NetworkPolicy/PVC, using the
same tenant-project pattern as the games cluster.

- `projects.yaml` — added `https://github.com/42WASD/42wasd-community-web.git`
  to `tenant-42wasd-admin` `sourceRepos` (its `prd-42wasd-admin` destination
  already existed).
- `apps/tenant-community-web.yaml` — Application, project
  `tenant-42wasd-admin`, source repo `42wasd-community-web.git` path
  `deploy/k8s`, dest `prd-42wasd-admin`, auto-sync + prune + selfHeal,
  `ServerSideApply=true`.

```bash
# AppProject is NOT Argo-managed -> apply manually (see gotcha above).
kubectl -n argocd apply -f infra/kubernetes/bootstrap/argocd/projects.yaml
kubectl -n argocd apply -f infra/kubernetes/bootstrap/argocd/apps/tenant-community-web.yaml
kubectl -n argocd get app tenant-community-web   # Synced
```

The Deployment mounts a writable `42wasd-data` PVC (nvme-fast, 1Gi, RWO) at
`/app/data` with `fsGroup: 1654` so `saveProfile` can persist `players.json`,
seeded by a non-root `seed-data` initContainer, and uses `strategy: Recreate`
(because the RWO volume can't be shared during a rolling update). Details and
verification live in the `42wasd-community-web` repo runbook
(`phase-18-production-hardening`).

> App health may read "Progressing" while the Deployment is actually Healthy:
> the Traefik Ingress does not populate `status.loadBalancer`, which ArgoCD's
> Ingress health hook treats as "not ready yet". Cosmetic only; the site serves
> HTTP 200 by hostname.