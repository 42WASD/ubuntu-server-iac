---
phase: 03-build-the-host/system-tuning-and-resource-safety/inotify-limits
---

# inotify limits — Phase 8.2

Covered in detail by the parent runbook
the Phase 8 runbook (`_runbook/03-build-the-host/phase-08-system-tuning.md`) §8.2.

```bash
# Raise inotify watcher limits for RKE2/container workloads
echo fs.inotify.max_user_instances=8192  | sudo tee /etc/sysctl.d/99-inotify.conf
echo fs.inotify.max_user_watches=1048576 | sudo tee -a /etc/sysctl.d/99-inotify.conf
sudo sysctl --system
```

Verified with `sysctl fs.inotify.max_user_instances fs.inotify.max_user_watches`.
