# Developer gets compromised

**Risk:**

```text
attacker has SSH as developer
```

**Expected boundary:**

```text
no sudo
no host Docker socket
cgroup limited
home quota limited
Kubernetes namespace RBAC
Pod Security restricted
Kyverno
NetworkPolicy
no other-tenant Secrets
```

If compromise immediately equals root, the platform design failed.

---
