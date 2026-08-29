---
phase: 03-build-the-host/storage-architecture/existing-install-path
---

# Storage: existing-install path — Phase 10

Covered in detail by the parent runbook
the Phase 10 runbook (`_runbook/03-build-the-host/phase-10-storage.md`) (§10.1 inspect-first and the
existing-install decision).

`alpha` came with Ubuntu already on LVM: the whole NVMe is one PV owned by
`ubuntu-vg` (100G root, ~1.76T free), the HDD completely unformatted. Rather
than repartition a live filesystem, LVs are carved from free extents of
`ubuntu-vg`, and separate VGs are created on new partitions (`vg_k8s_hdd`,
`vg_k8s_fast`). Verified topology recorded in parent §10.1.
