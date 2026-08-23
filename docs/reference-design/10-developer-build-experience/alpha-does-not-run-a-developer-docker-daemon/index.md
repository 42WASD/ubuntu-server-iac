---
order: 39
---

# Phase 39 — alpha does NOT run a developer Docker daemon

On `alpha`, normal developers need:

```text
git
language tools
venv
npm/pnpm
kubectl
Skaffold
Buildx client or wrapper CLI
```

They do not need:

```text
dockerd
/var/run/docker.sock
membership in docker group
```

This is deliberate.

---
