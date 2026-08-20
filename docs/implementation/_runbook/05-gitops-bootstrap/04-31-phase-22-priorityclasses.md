---
phase: 05-gitops-bootstrap/04-31-phase-22-priorityclasses
---
# Phase 22 — PriorityClasses
# Phase 22 — PriorityClasses

Created a small, deliberately non-inflated set of `PriorityClass` resources so
the scheduler can preempt low-value disposable workloads before starving
critical platform or production ones.

## 22.1 Manifests

`infra/kubernetes/platform/priorityclasses/priorityclasses.yaml`:

| PriorityClass               | value   | purpose |
| --------------------------- | ------- | ------- |
| `platform-critical-custom`  | 100000  | Critical platform workloads (platform admins). |
| `prod-high`                 | 20000   | Tenant production workloads. |
| `dev-normal`                | 1000    | Normal development workloads. |
| `build-low`                 | -1000   | Build / disposable workloads that yield first. |

No `globalDefault` is set, so ordinary pods get the default priority and
elevated classes must be requested explicitly.

Avoiding giant inflation: if every tenant could declare
`platform-critical`, priority is meaningless. Restricting who may use the
elevated classes is delegated to RBAC/Kyverno in a later phase.

Managed by a new Argo child app `platform-priorityclasses` (sync-wave `-20`,
so they exist before namespaces/quota apps). The `platform-root` app
auto-discovers it from `infra/kubernetes/bootstrap/argocd/apps`.

## 22.2 Applied via Argo CD

```bash
kubectl -n argocd get applications
# platform-priorityclasses  Synced  Healthy
```

```bash
kubectl get priorityclasses
# NAME                      VALUE
# platform-critical-custom  100000
# prod-high                 20000
# dev-normal                1000
# build-low                 -1000
```

The elevated `platform-critical-custom` class exists now; who may use it is
enforced later (RBAC / admission), not by the class itself.