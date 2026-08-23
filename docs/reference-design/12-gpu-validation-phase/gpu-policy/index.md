# GPU policy

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
mlops
  gpu-approved=true
  gpu-tier=shared
```

Kyverno rejects GPU resources elsewhere.

---
