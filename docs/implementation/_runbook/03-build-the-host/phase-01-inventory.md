---
phase: 03-build-the-host/01-10-phase-1-inventory-the-actual-machine
---
# Phase 1 — inventory the actual machine

**Intent:** Record reality before changing anything — storage, networking,
hardware. Never guess disk names.

**Commands run on `alpha`:**

```bash
hostnamectl
uname -a
cat /etc/os-release
lscpu
free -h

# Block devices (match on MODEL/SERIAL, never position)
lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,FSVER,MOUNTPOINTS,MODEL,SERIAL
findmnt
df -hT
df -ih

# LVM
sudo pvs
sudo vgs
sudo lvs -a -o +devices

# Networking
ip -br addr
ip route
resolvectl status

# PCIe devices (GPU + NICs)
lspci -nn
lspci -nn | grep -i -E 'nvidia|ethernet|network|storage|nvme'

# Storage health
sudo smartctl --scan
sudo nvme list 2>/dev/null || true
```

Saved to `~/platform-audit/alpha-baseline.txt`.

**What it produced:** `infra/inventory/host_vars/alpha.yml` — sanitized facts:
64 cores / 128 threads, 112 GiB RAM, 8 GiB swap, 2× RTX 3090, NVMe 1.9T
(Samsung PM9A1, OS root) + HDD 5.5T (ST6000NM0115, unallocated), LAN
`enp193s0` `192.168.8.132`, Tailscale `100.112.202.47`.

**Checkpoint 1 (verified):** identified the root device, both GPUs on PCIe, LVM
usage, free space, and the LAN NIC.