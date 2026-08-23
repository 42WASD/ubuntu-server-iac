---
order: 3
tracked: true
---

# Part III — Build the host

---

## Contents

- [Phase 0 — create the infrastructure repository first](create-the-infrastructure-repository-first/index.md)
- [Phase 1 — inventory the actual machine](inventory-the-actual-machine/index.md)
- [Phase 2 — update Ubuntu and install base administration tools](update-ubuntu-and-install-base-administration-tools/index.md)
  - [unattended security updates](update-ubuntu-and-install-base-administration-tools/unattended-security-updates/index.md)
- [Phase 3 — hostname, DNS, and local identity](hostname-dns-and-local-identity/index.md)
- [Phase 4 — users, groups, and sudo boundaries](users-groups-and-sudo-boundaries/index.md)
  - [sudo policy](users-groups-and-sudo-boundaries/sudo-policy/index.md)
  - [platform groups](users-groups-and-sudo-boundaries/platform-groups/index.md)
  - [no shared human account](users-groups-and-sudo-boundaries/no-shared-human-account/index.md)
- [Phase 5 — SSH hardening](ssh-hardening/index.md)
- [Phase 6 — Tailscale private management path](tailscale-private-management-path/index.md)
  - [Tailscale policy concept](tailscale-private-management-path/tailscale-policy-concept/index.md)
- [Phase 7 — host firewall](host-firewall/index.md)
- [Phase 8 — system tuning and resource safety](system-tuning-and-resource-safety/index.md)
  - [basic forwarding](system-tuning-and-resource-safety/basic-forwarding/index.md)
  - [inotify limits](system-tuning-and-resource-safety/inotify-limits/index.md)
  - [journald bound](system-tuning-and-resource-safety/journald-bound/index.md)
  - [disable swap initially](system-tuning-and-resource-safety/disable-swap-initially/index.md)
- [Phase 9 — developer CPU/RAM/PID limits on the host](developer-cpu-ram-pid-limits-on-the-host/index.md)
- [Phase 10 — storage architecture](storage-architecture/index.md)
  - [required LVM module](storage-architecture/required-lvm-module/index.md)
  - [fresh-install target](storage-architecture/fresh-install-target/index.md)
  - [existing-install path](storage-architecture/existing-install-path/index.md)
  - [desired logical layout](storage-architecture/desired-logical-layout/index.md)
  - [create dedicated RKE2 filesystem only when backing storage is known](storage-architecture/create-dedicated-rke2-filesystem-only-when-backing-storage-is-known/index.md)
  - [Kubernetes fast VG](storage-architecture/kubernetes-fast-vg/index.md)
  - [Kubernetes bulk VG](storage-architecture/kubernetes-bulk-vg/index.md)
- [Phase 11 — filesystem quotas for developer homes](filesystem-quotas-for-developer-homes/index.md)
- [Phase 12 — NVIDIA host driver baseline](nvidia-host-driver-baseline/index.md)
