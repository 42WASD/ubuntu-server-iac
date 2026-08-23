---
order: 2
---

# Developer has kubectl and tries privilege escalation

Protect against:

```text
privileged
hostPath
hostNetwork
hostPID
hostIPC
hostPort
dangerous RuntimeClass
unapproved NodePort
unapproved LoadBalancer
cluster-wide RBAC
```

Use:

```text
RBAC
PSA
Kyverno
restricted service account permissions
```

No single layer is sufficient.

---
