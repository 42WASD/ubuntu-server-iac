# Namespace reference

```text
SYSTEM / PLATFORM
kube-system
argocd
kyverno
openebs
monitoring
registry
security
ingress
build

42WASD-ADMIN
dev-42wasd-admin
prd-42wasd-admin

ML
mlops

GAMES (42wasd-admin)
dev-games-42wasd-admin   (ephemeral staging lane, deep-copy on demand)
prd-games-42wasd-admin   (canonical game lane)
```

## Why one shared `mlops` namespace

There is exactly one `mlops` namespace (not per-tenant `ml-jya0`/`gpu-jya0`)
because:

- ML/AI **models are heavy on GPU** and are a shared, expensive resource.
- Models are **consumed concurrently by any namespace** that wants to use them —
  the trained model weights are not owned by one tenant; many workloads across
  the platform call the same inference/embedding services.
- Maintaining separate ML namespaces per tenant would duplicate the shared
  model artifacts and fragment the GPU pool, wasting capacity.

So `mlops` is the single shared lane for GPU-backed model serving and ML
workloads. GPU allocation inside it is governed by quota and admission controls
rather than by namespace splitting.

---

---
