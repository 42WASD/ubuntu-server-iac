---
phase: 03-build-the-host/users-groups-and-sudo-boundaries/platform-groups
---

# Platform groups — Phase 4.1

Covered in detail by the parent runbook
the Phase 4 runbook (`_runbook/03-build-the-host/phase-04-users-groups.md`) §4.1 (incl. the post-hoc
group rename).

```bash
for g in ssh-users tenant-jya0 tenant-42wasd-admin gpu-approved; do
  sudo groupadd -f "$g"
done
sudo usermod -aG sudo,ssh-users jyao
```

`tenant-42admin` was later renamed `tenant-42wasd-admin` (`groupmod -n`) for
clarity; the name is consistent across infra + docs now.
