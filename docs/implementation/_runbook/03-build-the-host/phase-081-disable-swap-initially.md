---
phase: 03-build-the-host/system-tuning-and-resource-safety/disable-swap-initially
---

# Disable swap (initially) — Phase 8.1

Covered in detail by the parent runbook
the Phase 8 runbook (`_runbook/03-build-the-host/phase-08-system-tuning.md`) §8.1.

Summary of the change applied to `alpha`:

```bash
sudo swapoff -a
sudo sed -i 's|^/swap.img.*|# /swap.img was disabled for initial k8s deployment (Phase 8)|' /etc/fstab
```

Verified: `swapon --show` empty; fstab entry commented with the reason inline.
(Swap was re-enabled later as a deliberate feature after a host hard freeze —
see parent §8.6.)
