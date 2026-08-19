# Phase 51 — GPU policy

Once whole-GPU scheduling works:

```text
GPU0
    production / important workloads
    whole-GPU preferred

GPU1
    experimental shared workloads
    HAMi candidate
```

Only approved namespaces may request GPU resources.

Example namespace intent:

```text
gpu-jya0
  gpu-approved=true
  gpu-tier=shared

prod-jya0
  gpu-approved=true
  gpu-tier=prod
```

Kyverno rejects GPU resources elsewhere.

---
