---
phase: 03-build-the-host/10-15-phase-6-tailscale-private-management-path
---
# Phase 6 — Tailscale private management path

**Intent:** private management reachability to `alpha` via Tailscale (SSH, K8s
API, admin) without exposing public ports.

## 6.1 Check current status (already installed)

`tailscale` was installed and brought up earlier; verified live state:

```bash
tailscale status
tailscale ip -4
systemctl is-active tailscaled
tailscale version
```

**Verified on `alpha`:**
- `tailscaled` service **active**
- Tailscale version **1.102.3**
- IPv4 `100.112.202.47` (matches Phase 1 inventory)
- Tailnet peers present (beta, dev laptops, etc.)

**Checkpoint 5 (verified):**
- `ping 100.112.202.47` reachable from authorized laptop.
- SSH to `alpha` over tailnet works.