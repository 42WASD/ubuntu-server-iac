# Phase 20 — root GitOps application

Use a small **App-of-Apps** bootstrap rather than pointing one Application at an arbitrary directory tree.

Create:

```text
kubernetes/bootstrap/argocd/platform-root.yaml
kubernetes/bootstrap/argocd/apps/
```

Root application:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-root
  namespace: argocd
spec:
  project: default

  source:
    repoURL: "<YOUR_INFRA_GIT_REPO_URL>"
    targetRevision: main
    path: kubernetes/bootstrap/argocd/apps
    directory:
      recurse: true

  destination:
    server: https://kubernetes.default.svc
    namespace: argocd

  syncPolicy:
    automated:
      prune: true
      selfHeal: true

    syncOptions:
      - ServerSideApply=true
```

Then put child `Application` objects in `kubernetes/bootstrap/argocd/apps/`, one per platform subsystem.

Start with only namespaces:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-namespaces
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-20"
spec:
  project: default

  source:
    repoURL: "<YOUR_INFRA_GIT_REPO_URL>"
    targetRevision: main
    path: kubernetes/platform/namespaces

  destination:
    server: https://kubernetes.default.svc

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - ServerSideApply=true
```

Later add child Applications for:

```text
policy
storage
monitoring
registry
cloudflare
gpu
```

This is intentionally staged so a broken storage or GPU chart cannot prevent you from understanding whether the namespace/GitOps foundation itself works.

Apply:

```bash
kubectl apply -f kubernetes/bootstrap/argocd/platform-root.yaml
```

From here onward:

```text
if it belongs inside Kubernetes
    -> prefer Git + Argo
```

not:

```text
ssh alpha
helm install random-chart
forget what you did
```

---
