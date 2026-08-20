---
phase: 03-build-the-host/03-11-1-unattended-security-updates
---
# Phase 2.1 — unattended security updates

**Intent:** confirm automatic security updates are on, reboots controlled.

Covered by the `base` role (template deployed in Phase 2). Policy:
security-updates auto, reboot only in the 03:00 maintenance window.

**Checkpoint (verified):** `systemctl --failed`, `timedatectl`, `aa-status` all
clean.