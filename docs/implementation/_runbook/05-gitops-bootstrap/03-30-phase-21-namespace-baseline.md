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
- `tenants.yaml` — `dev-jya0`, `prd-jya0`, `dev-42wasd-admin`,
  `prd-42wasd-admin`, `mlops`, `dev-games-42wasd-admin`,
  `prd-games-42wasd-admin`, each labelled with `platform.tier: tenant` and Pod
  Security `restricted` (enforce/audit/warn).

`mlops` replaces the earlier per-tenant `ml-jya0`/`gpu-jya0` as a single shared
ML namespace: models are heavy on GPU and are consumed concurrently by any
namespace that wants to use them, so the model/GPU pool is shared rather than
duplicated per tenant (see reference namespace reference). The games lane is split into `dev-games-42wasd-admin` (ephemeral
staging) and `prd-games-42wasd-admin` (canonical) per the deep-copy-on-demand
methodology in Phase 53.

Infrastructure namespaces (`kube-system`, CNI, `argocd`) are **not** labelled
`restricted` — their trusted controllers need a less restrictive policy, per the
reference note.

## 21.2 Verified

```bash
kubectl get ns -l platform.tier=platform   # 7 platform namespaces Active
kubectl get ns -l platform.tier=tenant     # 7 tenant namespaces
kubectl get ns dev-games-42wasd-admin -o jsonpath='{.metadata.labels}'
# pod-security.kubernetes.io/{enforce,audit,warn}=restricted
```

The tenant namespaces carry the `restricted` Pod Security labels; platform
namespaces do not. The old `prod-jya0`/`ml-jya0`/`gpu-jya0`/`dev-42admin`/
`prod-42admin`/`games-42admin` namespaces are removed by Argo CD's prune since
they are no longer in the manifest.