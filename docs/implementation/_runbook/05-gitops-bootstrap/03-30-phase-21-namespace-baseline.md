---
phase: 05-gitops-bootstrap/03-30-phase-21-namespace-baseline
---
# Phase 21 — namespace baseline

Created the platform and tenant namespace baseline as code, managed by Argo CD
(the `platform-namespaces` child app from Phase 20).

## 21.1 Manifests

`infra/kubernetes/platform/namespaces/`:

- `platform.yaml` — `kyverno`, `openebs`, `monitoring`, `registry`, `security`,
  `ingress`, `build` (label `platform.tier: platform`).
- `tenants.yaml` — `dev-jya0`, `prod-jya0`, `ml-jya0`, `gpu-jya0`,
  `dev-42admin`, `prod-42admin`, `games-42admin`, each labelled with
  `platform.tier: tenant` and Pod Security `restricted` (enforce/audit/warn).

Infrastructure namespaces (`kube-system`, CNI, `argocd`) are **not** labelled
`restricted` — their trusted controllers need a less restrictive policy, per the
reference note.

## 21.2 Verified

```bash
kubectl get ns -l platform.tier=platform   # 7 platform namespaces Active
kubectl get ns -l platform.tier=tenant     # 7 tenant + demo-meme
kubectl get ns dev-42admin -o jsonpath='{.metadata.labels}'
# pod-security.kubernetes.io/{enforce,audit,warn}=restricted
```

The tenant namespaces carry the `restricted` Pod Security labels; platform
namespaces do not.