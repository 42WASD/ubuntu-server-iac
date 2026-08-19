# First real application acceptance test

Before calling the platform usable, deploy one small app that proves all major layers.

It should have:

```text
dev namespace
ResourceQuota
LimitRange
restricted Pod Security
NetworkPolicy
PVC
Service
Traefik route
Argo CD ownership
Harbor image
remote BuildKit build
Prometheus scrape or basic metrics
logs in Loki
Cloudflare public route
```

Developer workflow:

```text
SSH alpha
git clone
skaffold dev
change source
see dev Pod update
see logs
commit
CI test/build
promote image in Git
Argo deploys prod
```

If that loop works cleanly, your platform has proven the architecture rather than just installed software.

---
