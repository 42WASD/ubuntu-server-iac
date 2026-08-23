---
phase: 05-gitops-bootstrap/install-argo-cd-exactly-once-by-hand
---

# Phase 19 — install Argo CD exactly once by hand

**Intent:** do the one manual, minimal install of Argo CD that bootstraps
itself out of the paradox ("Argo cannot install itself before Argo exists").
Everything managed inside Kubernetes after this point goes through Git + Argo.

## 19.1 Pin the version

Latest release at install time was `v3.5.1` (verified against the GitHub
releases API). Kubernetes is `v1.36.3`, compatible.

```bash
export ARGOCD_VERSION="v3.5.1"
```

## 19.2 Install (server-side apply)

```bash
export KUBECONFIG=/home/jyao/.kube/config
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd --server-side --force-conflicts \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
```

Applied CRDs, ServiceAccounts, RBAC, ConfigMaps, Secrets, Services,
Deployments, a StatefulSet (`argocd-application-controller`), and NetworkPolicies.

## 19.3 Wait and verify

```bash
kubectl -n argocd rollout status deployment/argocd-server --timeout=180s
kubectl -n argocd get pods
```

All 7 pods `Running`:

```text
argocd-application-controller-0            1/1 Running
argocd-applicationset-controller-...       1/1 Running
argocd-dex-server-...                      1/1 Running
argocd-notifications-controller-...        1/1 Running
argocd-redis-...                           1/1 Running
argocd-repo-server-...                     1/1 Running
argocd-server-...                          1/1 Running
```

## 19.4 Initial admin access

Not exposed publicly (per design). Credentials:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

The `argocd-server` Service is `ClusterIP`, `80/TCP,443/TCP`. Verified reachable:

```bash
kubectl -n argocd port-forward svc/argocd-server 8443:443 &
curl -sk -o /dev/null -w 'HTTPS %{http_code}\n' https://127.0.0.1:8443/   # 200
```

## 19.5 Result

Argo CD v3.5.1 is running as the platform's GitOps owner. It is **not**
publicly exposed; temporary access is via `kubectl port-forward`. Next: Phase 20
root GitOps application (App-of-Apps bootstrap).