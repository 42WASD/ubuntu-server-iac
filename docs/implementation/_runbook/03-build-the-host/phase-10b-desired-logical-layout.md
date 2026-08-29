---
phase: 03-build-the-host/storage-architecture/desired-logical-layout
---

# Storage: desired logical layout — Phase 10

Covered in detail by the parent runbook
the Phase 10 runbook (`_runbook/03-build-the-host/phase-10-storage.md`) (§10.1 inspection, the layout
decision, and Checkpoint 7).

The realized layout on `alpha` (verified live 2026-08-29):

- `nvme0n1` (1.9T): OS PV `ubuntu-vg` (shrunk to ~1.12T, holding the 100G
  `ubuntu-lv` root and the 320G `rke2` LV) + `nvme0n1p4` → `vg_k8s_nvme`
  (754.6G, 538.6G free) for fast Kubernetes volumes.
- `sda` (5.5T HDD): 60% partitioned `k8s_bulk` → `vg_k8s_hdd` (3.27T, all
  free); ~2.2T left unallocated as emergency reserve.
- StorageClasses map `nvme-fast`/`nvme-db` → `vgpattern: vg_k8s_nvme.*` and
  `hdd-bulk` → `vg_k8s_hdd.*`.

Status note: the `fresh-install-target` variant remains `blocked`/n-a for
this host (Ubuntu is already installed); the existing-install path is what
was executed.
