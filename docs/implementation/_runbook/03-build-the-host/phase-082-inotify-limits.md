---
phase: 03-build-the-host/system-tuning-and-resource-safety/inotify-limits
---

# inotify limits — Phase 8.2

Covered in detail by the parent runbook
the Phase 8 runbook (`_runbook/03-build-the-host/phase-08-system-tuning.md`) §8.2.

```bash
# Deploy the inotify sysctl drop-in (source: scripts/system/)
sudo cp 99-platform-inotify.conf /etc/sysctl.d/
sudo sysctl --system
```

Live values on `alpha` (verified 2026-08-29):
`fs.inotify.max_user_instances = 8192`,
`fs.inotify.max_user_watches = 524288` (watches was already higher, so that
line was a no-op — the important change was instances 1024 → 8192).
