---
phase: 03-build-the-host/users-groups-and-sudo-boundaries/sudo-policy
---

# Sudo policy (minimal) — Phase 4.3

Covered in detail by the parent runbook
the Phase 4 runbook (`_runbook/03-build-the-host/phase-04-users-groups.md`) §4.3 (and the sudo-policy
subsection of the reference design).

Policy applied on `alpha`:

- `/etc/sudoers` kept untouched — no convenience `NOPASSWD` rules for tenants.
- Owner `jyao` retains `(ALL:ALL) ALL`.
- Tenants get **no** sudo; verified at Checkpoint 3: as a normal developer
  `sudo -l` → not allowed; as `jyao` `sudo -v` → works.
