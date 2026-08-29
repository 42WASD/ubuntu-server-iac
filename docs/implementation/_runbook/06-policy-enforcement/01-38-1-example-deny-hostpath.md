---
phase: 06-policy-enforcement/stage-policy-before-enforcing-it/example-deny-hostpath
---

# Example: deny hostPath — Phase 29.2

Covered in detail by the parent runbook
`_runbook/06-policy-enforcement/01-38-phase-29-stage-policy-before-enforcing-it.md`
(§29.2 policy table).

The `hostPath` deny is part of the `disallow-privileged-host-settings`
ClusterPolicy (`infra/kubernetes/platform/kyverno/policies/`), which blocks
`privileged`, `hostPath`, `hostNetwork`, `hostPID`, `hostIPC` in tenant
namespaces (`dev-*`, `prd-*`, `*-games-*`, `games-*`), running in **Audit**
mode with `background: true`.

Negative test fixture: `infra/kubernetes/policy-tests/hostpath-pod.yaml` —
applied in a dev namespace it must appear in the Kyverno policy report as a
violation while the pod still runs (Audit does not block).
