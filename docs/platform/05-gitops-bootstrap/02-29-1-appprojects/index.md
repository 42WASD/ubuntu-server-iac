# AppProjects

Create distinct projects:

```text
platform
tenant-jya0
tenant-42admin
```

Platform project can deploy cluster-wide resources.

Tenant projects should be constrained to authorized namespaces and repositories.

This creates a second boundary in addition to Kubernetes RBAC.

---
