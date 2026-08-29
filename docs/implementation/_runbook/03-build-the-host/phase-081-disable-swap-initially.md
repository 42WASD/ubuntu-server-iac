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

Verified at Phase 8.1 time: `swapon --show` empty; fstab entry commented with
the reason inline.

**Current live state (re-verified 2026-08-29): swap is ACTIVE again** —
re-enabled as a deliberate host safety net after a hard freeze caused by a
heavy host-side build into RAM-backed `/tmp` with zero swap headroom (parent
runbook §8.6). The reference page covers the full disable→re-enable cycle.
