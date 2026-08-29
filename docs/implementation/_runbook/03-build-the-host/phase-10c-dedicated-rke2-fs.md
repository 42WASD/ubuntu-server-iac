---
phase: 03-build-the-host/storage-architecture/create-dedicated-rke2-filesystem-only-when-backing-storage-is-known
---

# Storage: dedicated RKE2 filesystem only when backing storage is known — Phase 10

Covered in detail by the parent runbook
the Phase 10 runbook (`_runbook/03-build-the-host/phase-10-storage.md`) (§10.2 fast filesystem on NVMe and
§10.3 bulk VG on the HDD).

Principle applied: only create dedicated filesystems/VGs once the backing
storage is inspected and known (never guess disk topology). On `alpha` this
meant `lsblk/pvs/vgs/lvs` first, then the 320G `rke2` LV on `ubuntu-vg`
(xfs, mounted at `/var/lib/rancher/rke2`), `vg_k8s_hdd` (HDD, 0–60%) and
`vg_k8s_nvme` (NVMe, after the PV/partition resize) — sizes verified with
`vgs` before proceeding (Checkpoint 7). Live check 2026-08-29: `rke2` LV
320G at 8% usage, mounted `noatime`, noquota.
