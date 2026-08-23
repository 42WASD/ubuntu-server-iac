---
order: 7
---

# "Bad idea" reference

Bad:

```text
shared SSH account for humans
developer sudo
developer cluster-admin
host Docker socket
privileged tenant Pods
free hostPath
no resource requests/limits
no quotas
everything on /
build cache on alpha
registry on root filesystem
plain-text secrets in Git
floating latest versions
public Kubernetes API
public Grafana/Argo without an access layer
Cloudflare Tunnel assumed to proxy all UDP games for free
3090 treated as MIG-isolated
single-node called HA
```

---
