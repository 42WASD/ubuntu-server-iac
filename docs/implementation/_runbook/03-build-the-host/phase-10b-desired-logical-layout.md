---
phase: 03-build-the-host/storage-architecture/desired-logical-layout
---

# Storage: desired logical layout — Phase 10

Covered in detail by the parent runbook
the Phase 10 runbook (`_runbook/03-build-the-host/phase-10-storage.md`) (§10.1 inspection, the layout
decision, and Checkpoint 7).

The realized layout on `alpha`:

- `nvme0n1` (1.9T): OS PV `ubuntu-vg` (shrunk to 1150G) + new `k8s_fast`
  partition → `vg_k8s_fast` for fast Kubernetes volumes.
- `sda` (5.5T HDD): 60% partitioned `k8s_bulk` → `vg_k8s_hdd` (~3.27T) for
  bulk volumes; ~2.2T left unallocated as emergency reserve.
- Root LV stays 100G; quotas protect it (Phase 11).

Status note: the `fresh-install-target` variant remains `blocked`/n-a for
this host (Ubuntu is already installed); the existing-install path is what
was executed.
