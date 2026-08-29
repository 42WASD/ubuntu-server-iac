---
phase: 03-build-the-host/system-tuning-and-resource-safety/journald-bound
---

# journald storage bound — Phase 8.4

Covered in detail by the parent runbook
the Phase 8 runbook (`_runbook/03-build-the-host/phase-08-system-tuning.md`) §8.4.

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
sudo cp 50-platform.conf /etc/systemd/journald.conf.d/
sudo systemctl restart systemd-journald
```

Bounds: `SystemMaxUse=4G`, `SystemKeepFree=8G`, `RuntimeMaxUse=1G`,
`MaxRetentionSec=14day`, `Compress=yes` — the journal can never starve the
node disk. Verified with `journalctl --disk-usage`.
