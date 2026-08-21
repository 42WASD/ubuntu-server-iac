---
phase: 06-policy-enforcement/00-37-phase-28-install-kyverno-through-argo-cd
---
# Phase 28 — install Kyverno through Argo CD

**Intent:** install Kyverno (CNCF policy engine) into its own `kyverno`
namespace via Argo CD, using a **pinned** Helm chart version, on a single-node
scale.

Reference: `docs/reference-design/build/06-policy-enforcement/00-37-phase-28-install-kyverno-through-argo-cd/`

## 28.1 Pre-flight (verified live)

- `kyverno` namespace already exists and is Argo-managed via
  `infra/kubernetes/platform/namespaces/platform.yaml`
  (`platform.tier: platform`, no restricted Pod Security label).
- No Helm repository is configured in Argo CD yet; this phase adds the first
  multi-source (chart + values) Application.
- Latest pinned chart chosen: **`kyverno` 3.9.0** (app v1.20.0, Aug 2026).

## 28.2 Files added

- `infra/kubernetes/platform/kyverno/values.yaml` — chart values:
  - `replicaCount: 1` (single-node; 3 replicas on one node ≠ HA).
  - namespace exclusions so Kyverno stays recoverable (`kyverno`,
    `kube-system`, `argocd`).
- `infra/kubernetes/bootstrap/argocd/apps/platform-kyverno.yaml` — Argo CD
  `Application` (project `platform`, sync-wave `-3`), multi-source:
  - Helm chart from `https://kyverno.github.io/kyverno`, `3.9.0`.
  - the repo as a `ref: values` source so it can load
    `$values/infra/kubernetes/platform/kyverno/values.yaml`.

## 28.3 How it is wired

`platform-root` (app-of-apps) recurses over
`infra/kubernetes/bootstrap/argocd/apps`, so adding
`platform-kyverno.yaml` there auto-creates the Application on the next sync.

Sync options: `ServerSideApply=true`, `CreateNamespace=true`.

## 28.4 Verified

```bash
kubectl -n kyverno get deploy
```

Expected after the Application syncs:

```text
kyverno-admission-controller   1/1   Running
kyverno-background-controller  1/1   Running
kyverno-cleanup-controller     1/1   Running
kyverno-reports-controller     1/1   Running
```

**Live result** (after `platform-root` hard-refresh picked up the new
Application):

```text
NAME                                            READY   STATUS     AGE
kyverno-admission-controller-...                1/1     Running    79s
kyverno-background-controller-...               1/1     Running    79s
kyverno-cleanup-controller-...                  1/1     Running    79s
kyverno-reports-controller-...                  1/1     Running    79s
platform-kyverno-migrate-resources-...          0/1     Completed  24s
```

`platform-kyverno` Application: **Healthy** (OutOfSync is the transient
"chart freshly applied" state — Argo `automated` self-heal converges it).

No policies are enabled yet — that is Phase 29 (stage in Audit first).