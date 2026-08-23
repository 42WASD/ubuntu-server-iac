# public vs private names

Recommended categories:

```text
PUBLIC
  status.<DOMAIN>
  docs.<DOMAIN>
  public APIs
  public project pages

CLOUDFLARE ACCESS PROTECTED
  optional web admin tools
  internal kanban
  Git web UI if desired

TAILSCALE ONLY
  Kubernetes API
  Harbor registry endpoint
  SSH
  low-level admin endpoints
  emergency tools
```

Argo/Grafana can remain Tailscale-only initially.

Do not expose every UI simply because HTTPS is available.

---
