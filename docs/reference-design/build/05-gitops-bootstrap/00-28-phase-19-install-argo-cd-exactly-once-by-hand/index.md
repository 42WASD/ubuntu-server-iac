# Phase 19 — install Argo CD exactly once by hand

Argo CD becomes the owner of Kubernetes configuration **after bootstrap**.

The bootstrap paradox is unavoidable:

```text
Argo cannot install itself before Argo exists
```

Do one minimal manual install.

Choose and pin an Argo CD version.

Example:

```bash
export ARGOCD_VERSION="<PINNED_ARGOCD_VERSION>"

kubectl create namespace argocd

kubectl apply \
  -n argocd \
  --server-side \
  --force-conflicts \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
```

Wait:

```bash
kubectl -n argocd rollout status deployment/argocd-server
kubectl -n argocd get pods
```

Do **not** expose Argo CD publicly yet.

Access temporarily with:

```bash
kubectl -n argocd port-forward svc/argocd-server 8443:443
```

---
