---
phase: 03-build-the-host/system-tuning-and-resource-safety/basic-forwarding
---

# Basic IP forwarding — Phase 8.3

Covered in detail by the parent runbook
the Phase 8 runbook (`_runbook/03-build-the-host/phase-08-system-tuning.md`) §8.3.

```bash
# Deploy the network sysctl drop-in (source: scripts/system/)
sudo cp 99-platform-network.conf /etc/sysctl.d/
sudo sysctl --system
```

Pins `net.ipv4.ip_forward = 1` and `net.ipv6.conf.all.forwarding = 1`
(both were already on for alpha — confirm/no-op, but pinned so future config
resets can't silently flip them). No masquerading/general routing added.
