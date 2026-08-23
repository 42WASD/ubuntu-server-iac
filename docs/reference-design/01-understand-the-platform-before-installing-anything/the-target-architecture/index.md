---
order: 1
---

# The target architecture

```text
                                  INTERNET
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 | HTTP/HTTPS                            | GAME TCP/UDP
                 v                                       v
          Cloudflare Edge                         UAE relay VPS
     DNS / CDN / WAF / Access                    public IP
                 |                                       |
         Cloudflare Tunnel                         WireGuard
                 |                                       |
                 +-------------------+-------------------+
                                     |
                                     v
+----------------------------------------------------------------------------------+
| ALPHA                                                                            |
| Ubuntu 26.04 LTS Server                                                          |
|                                                                                  |
|  Tailscale                                                                       |
|   + SSH                                                                           |
|   + private Kubernetes API                                                        |
|   + private admin endpoints                                                       |
|                                                                                  |
|  Linux developer environment                                                     |
|   + individual users                                                             |
|   + venv/npm/cargo/go/etc.                                                       |
|   + per-user cgroup limits                                                       |
|   + filesystem quotas                                                            |
|   + kubectl                                                                      |
|   + Skaffold / Buildx client                                                     |
|                       |                                                          |
|                       +----------------------- remote build -------------------+  |
|                                                                                  |
|  RKE2                                                                            |
|   + Cilium                                                                       |
|   + Traefik                                                                      |
|   + Argo CD                                                                      |
|   + OpenEBS LocalPV LVM                                                          |
|   + Kyverno                                                                      |
|   + Harbor                                                                       |
|   + Prometheus/Grafana/Loki/Alloy                                                |
|   + dev/prod/ml/gpu/game namespaces                                              |
|   + approved GPU workloads                                                       |
+----------------------------------------------------------------------------------+
                                        |
                                        | BuildKit protocol over private network
                                        v
+----------------------------------------------------------------------------------+
| BUILD01                                                                          |
| Ubuntu                                                                           |
|                                                                                  |
| LXD / KVM                                                                        |
|   + builder-jya0          -> rootless BuildKit + persistent cache                |
|   + builder-42admin       -> rootless BuildKit + persistent cache                |
|   + untrusted-ci VM       -> disposable / stronger isolation                     |
+----------------------------------------------------------------------------------+
```

---
