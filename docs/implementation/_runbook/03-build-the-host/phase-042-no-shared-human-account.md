---
phase: 03-build-the-host/users-groups-and-sudo-boundaries/no-shared-human-account
---

# No shared human account — Phase 4.2/4.4

Covered in detail by the parent runbook
the Phase 4 runbook (`_runbook/03-build-the-host/phase-04-users-groups.md`) §4.2 and §4.4.

Every human gets a **named account** (no shared logins): `jyao-42admin`
(UID 1001, groups `ssh-users tenant-42wasd-admin`) plus tenant accounts
`ehammoud`, `mayan`, `mtangalv` (§4.4). Group membership (not shared
credentials) is what grants tenant access; home dirs are quota-bound
(Phase 11).
