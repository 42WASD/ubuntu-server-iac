---
phase: 05-gitops-bootstrap/08-35-phase-26-rbac/production-is-intentionally-different
---
# production is intentionally different (26.2)

In prod namespaces developers are read-only (`get`/`list`/`watch`/`logs`/
`events`, possibly port-forward). Application writes come exclusively from
Argo CD. A principal that can create arbitrary prod Pods can mount Secrets
from that namespace even if RBAC denies direct `get secret`, so giving devs
write access in prod would make the "cannot read Secret" boundary meaningless.

Verified with `kubectl auth can-i` (as the tenant group):

```bash
kubectl auth can-i create deployments -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
kubectl auth can-i get pods -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # yes
kubectl auth can-i get secrets -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
```