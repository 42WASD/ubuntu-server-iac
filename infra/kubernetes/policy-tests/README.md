# Policy tests (Phase 30)

These are **intentionally-bad** manifests used to *prove* the platform rejects
forbidden workloads. They are fixtures — **do not apply them** to a real tenant
namespace in the normal course of work.

## Philosophy

The platform is not "secure because YAML exists." It is secure when the
forbidden test *actually fails*.

## Fixtures

| File | Violates | Should be caught by |
|---|---|---|
| `privileged-pod.yaml` | `privileged: true` | `disallow-privileged-host-settings` / restricted PSA |
| `hostpath-pod.yaml` | hostPath volume `/` | `disallow-privileged-host-settings` / restricted PSA |
| `hostnetwork-pod.yaml` | `hostNetwork: true` | `disallow-privileged-host-settings` / restricted PSA |
| `no-resource-limits.yaml` | no requests/limits | `require-resource-limits` |
| `nodeport-service.yaml` | `type: NodePort` | `restrict-exposure-and-image-tags` |
| `unapproved-registry-prod.yaml` | unapproved registry + `:latest` in prod | `require-approved-registry-in-prod` |
| `unapproved-priorityclass.yaml` | disallowed PriorityClass | `restrict-storage-priority-gpu` |

## How to validate

Policies are in **Audit** mode (Phase 29). Two levels of proof:

1. **Admission-time deny** (PSA `restricted` enforce already blocks
   privileged/hostPath/hostNetwork): `kubectl apply` a fixture and observe the
   admission rejection.
2. **Kyverno report** (audit): the forbidden resource is flagged in the
   `PolicyReport` / `ClusterPolicyReport`.

Before flipping any policy to **Enforce**, confirm the tests it targets
actually fail here.