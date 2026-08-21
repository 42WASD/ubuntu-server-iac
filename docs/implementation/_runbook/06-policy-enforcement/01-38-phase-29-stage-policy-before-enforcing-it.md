---
phase: 06-policy-enforcement/01-38-phase-29-stage-policy-before-enforcing-it
---
# Phase 29 — stage policy before enforcing it

**Intent:** add Kyverno policies in **Audit** mode first, inspect reports, then
(only after the platform/tenant workloads are clean) flip selected rules to
**Enforce**. Do not enable 25 deny policies in one commit.

Reference: `docs/reference-design/build/06-policy-enforcement/01-38-phase-29-stage-policy-before-enforcing-it/`

## 29.1 Kyverno API note (v1.19)

Kyverno 1.19 deprecates the top-level `spec.validationFailureAction` in favour
of the per-rule `validate.failureAction` (values `Audit`/`Enforce`). Phase 29
uses the modern form so the switch to Enforce later is a one-line, per-rule
change. The legacy `spec.validationFailureAction: Audit` still works but emits
a deprecation warning; we set it for the policy-level default.

## 29.2 Policies staged (all Audit)

Files under `infra/kubernetes/platform/kyverno/policies/`:

| Policy file | Controls |
|---|---|
| `disallow-privileged-host-settings.yaml` | privileged, hostPath, hostNetwork, hostPID, hostIPC |
| `require-resource-limits.yaml` | requests/limits on every container |
| `restrict-exposure-and-image-tags.yaml` | NodePort, LoadBalancer, hostPort, `:latest` in prod, no-digest in prod |
| `restrict-storage-priority-gpu.yaml` | approved StorageClasses, PriorityClasses, no GPU without approval |
| `require-approved-registry-in-prod.yaml` | prod images from approved registries |

All rules match tenant namespaces (`dev-*`, `prd-*`, `*-games-*`, `games-*`)
and run with `background: true` in **Audit** (non-blocking) mode.

## 29.3 Wiring (Argo CD)

- `kustomization.yaml` bundles the 5 ClusterPolicies.
- `infra/kubernetes/bootstrap/argocd/apps/platform-kyverno-policies.yaml`
  adds Application `platform-kyverno-policies` (project `platform`, sync-wave
  `-2`) so `platform-root` (app-of-apps) applies them.

## 29.4 Verified

```bash
kubectl -n argocd get application platform-kyverno-policies
kubectl get clusterpolicy
```

Expected: all 5 ClusterPolicies present, status `Ready`, mode Audit. No policy
is enforcing yet — that is the Phase 30 test gate before any rule flips to
Enforce.

## 29.5 Next step (Phase 29 → 30)

Inspect `kubectl get policyreport` / `clusterrreport` after policies are live
to confirm no tenant workload is unexpectedly flagged, then Phase 30 creates
intentionally-bad manifests to prove the deny rules actually fire.