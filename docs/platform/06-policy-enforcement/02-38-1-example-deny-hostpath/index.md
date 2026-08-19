# example: deny hostPath

Concept:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-hostpath
spec:
  validationFailureAction: Audit
  background: true
  rules:
    - name: hostpath
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - "dev-*"
                - "prod-*"
                - "games-*"
      validate:
        message: "Tenant Pods may not use hostPath."
        pattern:
          spec:
            =(volumes):
              - X(hostPath): "null"
```

Treat that as a starting example; use the pinned Kyverno release's documented policy syntax and tests before Enforce.

---
