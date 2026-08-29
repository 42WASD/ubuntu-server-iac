---
phase: 03-build-the-host/storage-architecture/kubernetes-fast-vg
---

# Storage: Kubernetes fast VG — Phase 10.4

Covered in detail by the parent runbook
the Phase 10 runbook (`_runbook/03-build-the-host/phase-10-storage.md`) §10.4 (created after owner override).

```bash
# Shrink PV metadata first (removes only free extents — never touches LV data)
sudo pvresize --setphysicalvolumesize 1150G /dev/nvme0n1p3
# Shrink the physical partition to match, then carve the fast VG partition
sudo parted /dev/nvme0n1 unit MiB resizepart 3 1180800
sudo parted /dev/nvme0n1 unit MiB mkpart primary 1180800MiB 100%
sudo parted /dev/nvme0n1 name 4 k8s_fast
sudo pvcreate /dev/nvme0n1p4 && sudo vgcreate vg_k8s_fast /dev/nvme0n1p4
```

Owner-approved on a fresh server; every size verified with `pvs/vgs/lvs` and
`parted unit MiB print` before each step.
