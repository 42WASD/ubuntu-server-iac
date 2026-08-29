---
phase: 03-build-the-host/storage-architecture/required-lvm-module
---

# Storage: required LVM module (dm_snapshot) — Phase 10.5

Covered in detail by the parent runbook
the Phase 10 runbook (`_runbook/03-build-the-host/phase-10-storage.md`) §10.5.

```bash
sudo modprobe dm_snapshot
echo dm_snapshot | sudo tee /etc/modules-load.d/openebs-lvm.conf
```

OpenEBS LocalPV LVM needs `dm-snapshot`; the modules-load file makes it load
at every boot.
