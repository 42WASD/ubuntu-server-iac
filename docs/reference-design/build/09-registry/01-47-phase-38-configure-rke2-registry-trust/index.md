# Phase 38 — configure RKE2 registry trust

RKE2 uses:

```text
/etc/rancher/rke2/registries.yaml
```

for registry mirror/auth/TLS configuration.

Prefer a real TLS certificate.

Avoid an insecure HTTP registry.

After modifying registry configuration:

```bash
sudo systemctl restart rke2-server
```

Then test a harmless image pull from Harbor.

---
