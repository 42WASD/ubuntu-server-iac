# LimitRange

Example:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-defaults
  namespace: dev-42wasd-admin
spec:
  limits:
    - type: Container

      defaultRequest:
        cpu: 250m
        memory: 256Mi
        ephemeral-storage: 512Mi

      default:
        cpu: "2"
        memory: 2Gi
        ephemeral-storage: 4Gi

      max:
        cpu: "4"
        memory: 8Gi
        ephemeral-storage: 20Gi
```

This prevents the common mistake:

```yaml
resources: {}
```

from silently turning every tenant workload into an unbounded consumer.

---
