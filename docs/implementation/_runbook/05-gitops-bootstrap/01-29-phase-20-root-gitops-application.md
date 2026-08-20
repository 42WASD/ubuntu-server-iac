---
phase: 05-gitops-bootstrap/01-29-phase-20-root-gitops-application
---
# Phase 20 — root GitOps application

**Intent:** stand up the **App-of-Apps** bootstrap so Argo CD owns Kubernetes
configuration from here on. One root Application (`platform-root`) watches a
directory of child `Application` objects.

## 20.1 Manifests

Created under `infra/kubernetes/bootstrap/argocd/`:

- `platform-root.yaml` — root App-of-Apps Application pointing at
  `infra/kubernetes/bootstrap/argocd/apps` (recurse).
- `apps/platform-namespaces.yaml` — child Application for the namespace
  baseline, `sync-wave -20` so namespaces exist first.
- `projects.yaml` — AppProjects: `platform`, `tenant-jya0`,
  `tenant-42wasd-admin`.

The repo is public, so Argo CD clones it over HTTPS with no stored credential.

```bash
kubectl apply -f infra/kubernetes/bootstrap/argocd/projects.yaml
kubectl apply -f infra/kubernetes/bootstrap/argocd/platform-root.yaml
```

## 20.2 Result

```bash
kubectl -n argocd get applications
```

```text
NAME                  SYNC STATUS   HEALTH STATUS
platform-namespaces   Synced        Healthy
platform-root         Synced        Healthy
```

Both synced automatically (automated sync, prune + selfHeal, server-side
apply). The child `platform-namespaces` app was created by the root app with no
manual `kubectl apply`.

## 20.3 From here on

```text
if it belongs inside Kubernetes
    -> prefer Git + Argo
```

not manual `kubectl apply`. This was the last hand-applied piece of platform
config (besides Argo CD itself, Phase 19).