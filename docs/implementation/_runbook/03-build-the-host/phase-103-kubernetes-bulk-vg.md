---
phase: 03-build-the-host/storage-architecture/kubernetes-bulk-vg
---

# Storage: Kubernetes bulk VG — Phase 10.3

Covered in detail by the parent runbook
the Phase 10 runbook (`_runbook/03-build-the-host/phase-10-storage.md`) §10.3.

```bash
sudo parted -s /dev/sda mklabel gpt
sudo parted -s /dev/sda mkpart primary 0% 60%
sudo parted -s /dev/sda name 1 k8s_bulk
sudo pvcreate /dev/sda1
sudo vgcreate vg_k8s_hdd /dev/sda1
```

Verified: `vgs vg_k8s_hdd` → ~3.27T free. ~2.2T of the HDD deliberately left
unallocated as emergency reserve (LVM free extents beat a 100%-allocated
disk in a crisis).
