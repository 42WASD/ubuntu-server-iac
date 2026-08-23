# Traefik routing

Prefer Gateway API/HTTPRoute where your installed RKE2 Traefik version supports your required feature cleanly.

Simple HTTP mental model:

```text
Gateway
    |
HTTPRoute host = api.jya0.<DOMAIN>
    |
Service
    |
Pods
```

Do not use NodePort as the normal public web publication mechanism.

Cloudflare Tunnel should reach the in-cluster ingress path privately.

---
