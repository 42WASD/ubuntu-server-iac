---
order: 46
---

# Phase 46 — Cloudflare Tunnel

Do this only after an internal service works.

Path:

```text
Browser
-> Cloudflare
-> cloudflared
-> Traefik
-> Service
-> Pod
```

Deploy `cloudflared` inside Kubernetes through Argo CD.

Keep its tunnel token/credential in a Kubernetes Secret managed through an encrypted secret workflow.

Important:

```text
tunnel token = credential
```

Do not commit it in plaintext.

---
