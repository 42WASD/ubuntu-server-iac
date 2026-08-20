# Phase 21 — namespace baseline

Create platform namespaces:

```text
argocd
kyverno
openebs
monitoring
registry
security
ingress
build
```

Tenant namespaces:

```text
dev-jya0
prod-jya0
ml-jya0
gpu-jya0

dev-42admin
prod-42admin
games-42admin
```

For tenant application namespaces, apply Pod Security labels.

Start dev namespaces with:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev-42admin
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Infrastructure namespaces may need a less restrictive policy for trusted controllers.

Do **not** label `kube-system` or CNI namespaces `restricted` without understanding their workload requirements.

---
