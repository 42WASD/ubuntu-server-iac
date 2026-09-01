---
phase: 05-gitops-bootstrap/namespace-baseline
---

# Phase 21 — namespace baseline

Created the platform and tenant namespace baseline as code, managed by Argo CD
(the `platform-namespaces` child app from Phase 20).

## 21.1 Manifests

`infra/kubernetes/platform/namespaces/`:

- `platform.yaml` — `kyverno`, `openebs`, `monitoring`, `registry`, `security`,
  `ingress`, `build` (label `platform.tier: platform`).
- `tenants.yaml` — `dev-42wasd-admin`,
  `prd-42wasd-admin`, `mlops`, `dev-games-42wasd-admin`,
  `prd-games-42wasd-admin`, each labelled with `platform.tier: tenant` and Pod
  Security `restricted` (enforce/audit/warn).
  (The original `dev-jya0`/`prd-jya0` entries were removed on 2026-09-01 — see
  the decommission note at the end of this file.)

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

## 21.3 Decommission note (2026-09-01): jya0 tenant namespaces removed

The `dev-jya0` and `prd-jya0` namespaces were deleted (tenant `jya0`
deactivated). Both were empty — no workloads, PVCs or PVs — so removal was
pure Git + Argo CD prune, no data migration needed:

1. Removed `dev-jya0`/`prd-jya0` from `tenants.yaml` and deleted the
   per-tenant platform manifests `quotas/jya0.yaml`, `limitranges/jya0.yaml`,
   `networkpolicies/jya0.yaml`, `rbac/jya0.yaml` (they referenced the deleted
   namespaces and would fail the Argo apps' sync otherwise).
2. Removed `dev-jya0`/`prd-jya0` from the CCNP selector in
   `networkpolicies/00-allow-kube-apiserver.yaml` (and its comment list).
3. `platform-namespaces` / `platform-quotas` / `platform-limitranges` /
   `platform-networkpolicies` / `platform-rbac` all run with
   `automated.prune=true selfHeal=true`, so on the next refresh Argo CD
   deleted the two namespaces and their in-namespace baseline objects
   (default-deny, allow-cluster-dns, namespace-budget, tenant-developer/
   tenant-reader Roles + RoleBindings).

Deliberately NOT removed (kept per owner decision, 2026-09-01): the
`tenant-jya0` Argo CD AppProject, the `tenant-jya0` Linux group, and the
`tenant-jya0` team in the Dex GitHub connector — the tenant identity is
retained so it can be re-enabled later.

Note: the two namespaces were deleted the same day the owner's disk quota was
raised (10/15 GiB — see phase-11 runbook); the old 10 GiB hard limit was
blocking `git rm` index writes at the time.