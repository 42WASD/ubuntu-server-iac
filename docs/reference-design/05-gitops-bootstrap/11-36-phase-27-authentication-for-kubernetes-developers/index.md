# Phase 27 — authentication for Kubernetes developers

Do not distribute the admin kubeconfig.

Short-term, for a small team, you can issue individual Kubernetes client credentials.

Long-term, use OIDC.

Target model:

```text
identity provider
    -> group tenant-jya0
    -> group tenant-42admin
    -> group gpu-approved
```

RKE2 API is reachable only through private management networking.

OIDC handles identity.

Kubernetes RBAC handles authorization.

This step may be postponed until the first external developer exists, but **do not solve it by copying `/etc/rancher/rke2/rke2.yaml`**.

---
