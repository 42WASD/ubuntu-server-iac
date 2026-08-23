---
order: 21
---

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
prd-jya0

dev-42wasd-admin
prd-42wasd-admin

mlops

dev-games-42wasd-admin   (ephemeral staging lane)
prd-games-42wasd-admin   (canonical game lane)
```

`dev-games-42wasd-admin` is a lightweight, on-demand staging lane for deep-
copying one game server at a time (see Phase 53); it is throwaway and excluded
from canonical backups.

For tenant application namespaces, apply Pod Security labels.

Start dev namespaces with:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev-42wasd-admin
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Infrastructure namespaces may need a less restrictive policy for trusted controllers.

Do **not** label `kube-system` or CNI namespaces `restricted` without understanding their workload requirements.

---
