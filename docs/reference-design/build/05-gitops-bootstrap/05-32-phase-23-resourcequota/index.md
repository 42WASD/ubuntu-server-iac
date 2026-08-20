# Phase 23 — ResourceQuota

Example `dev-42admin`:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: namespace-budget
  namespace: dev-42admin
spec:
  hard:
    requests.cpu: "4"
    limits.cpu: "8"

    requests.memory: 8Gi
    limits.memory: 16Gi

    requests.ephemeral-storage: 20Gi
    limits.ephemeral-storage: 40Gi

    requests.storage: 100Gi

    pods: "40"
    services: "15"
    persistentvolumeclaims: "10"
    configmaps: "50"
    secrets: "30"
```

Remember:

```text
quota = ceiling
quota != reservation
```

The sum of namespace ceilings may exceed node capacity.

Actual scheduling still depends on real requested resources.

---
