---
phase: 03-build-the-host/19-19-phase-10-storage-architecture
---
# Phase 10 — storage architecture

**Intent:** give Kubernetes a safe, extensible storage layout: a dedicated fast
RKE2 data filesystem, a bulk K8s VG for volumes, and deliberate free reserves
so future-you can extend without pain. On `alpha` this followed the
**existing-install path** (Ubuntu already installed on LVM) — we create LVs
from free extents and add VGs; we do NOT repartition a live filesystem just to
make the diagram pretty.

## 10.1 Inspect first (never guess)

```bash
lsblk -f
sudo pvs ; sudo vgs ; sudo lvs
```

**Actual topology on alpha:**

<table>
<thead><tr><th>Disk</th><th>Size</th><th>Role</th><th>State</th></tr></thead>
<tbody>
<tr><td><code>nvme0n1</code></td><td>1.9T NVMe</td><td>OS</td><td><code>ubuntu-vg</code> PV = whole disk, 100G root, <strong>1.76T free</strong></td></tr>
<tr><td><code>sda</code></td><td>5.5T HDD</td><td>bulk</td><td>completely unformatted</td></tr>
</tbody>
</table>

**Why inspect:** the design explicitly says don't casually shrink a live
filesystem. The NVMe is one big PV owned by `ubuntu-vg`, so a *separate* fast
NVMe VG is impossible without a repartition → we create LVs inside `ubuntu-vg`
instead.

## 10.2 Dedicated RKE2 filesystem (fast, on NVMe)

**Why:** RKE2's data dir must be on fast storage with its own headroom, so
runaway etcd/containerd can't fill root.

```bash
# 320G logical volume from ubuntu-vg free extents (NOT a partition shrink)
sudo lvcreate -L 320G -n rke2 ubuntu-vg
# format XFS (defaults,noatime)
sudo mkfs.xfs /dev/ubuntu-vg/rke2

sudo mkdir -p /var/lib/rancher/rke2
echo '/dev/ubuntu-vg/rke2 /var/lib/rancher/rke2 xfs defaults,noatime 0 2' | sudo tee -a /etc/fstab
sudo mount -a
sudo systemctl daemon-reload   # systemd cached the old fstab
```

**Verified:**
```bash
findmnt /var/lib/rancher/rke2   # -> xfs, rw,noatime
df -hT /var/lib/rancher/rke2    # -> 320G, 314G avail
```

## 10.3 Bulk Kubernetes VG on the HDD

**Why:** bulk/cheap K8s volumes go on the HDD; we give it ~60% (~3.3T) and
leave the rest as emergency reserve (LVM free extents are more useful in a
crisis than a 100%-allocated disk).

```bash
# GPT table + one 0-60% partition, labeled for intent
sudo parted -s /dev/sda mklabel gpt
sudo parted -s /dev/sda mkpart primary 0% 60%
sudo parted -s /dev/sda name 1 k8s_bulk

sudo pvcreate /dev/sda1
sudo vgcreate vg_k8s_hdd /dev/sda1
```

**Verified:** `vgs vg_k8s_hdd` → `3.27t`, `3.27t` free. ~2.2T left unallocated
on the HDD as emergency reserve.

## 10.4 Fast NVMe VG (created after owner override)

**Why override:** the owner decided a fast NVMe VG for Kubernetes is important
for workload performance, and since this is a brand-new server, reallocating
now is low-risk. The design's "don't shrink a live filesystem" rule exists to
protect production data; on a fresh box with plenty of headroom we can do it
safely.

Migration steps (all sizes verified first with `pvs/vgs/lvs` and
`parted unit MiB print`):

```bash
# 1) Shrink the LVM PV metadata FIRST (only free extents are removed —
#    this is safe; it never touches data in the existing LVs).
sudo pvresize --setphysicalvolumesize 1150G /dev/nvme0n1p3
#    -> PV now 1150G, ubuntu-vg still has 730G free

# 2) Shrink the physical partition p3 to match the PV (from ~1905G to 1150G).
sudo parted /dev/nvme0n1 unit MiB resizepart 3 1180800

# 3) Create a new partition p4 for the fast VG (1180800 -> 100%)
sudo parted /dev/nvme0n1 unit MiB mkpart primary 1180800MiB 100%
sudo parted /dev/nvme0n1 name 4 k8s_fast
sudo partprobe /dev/nvme0n1

# 4) Create the fast PV + VG
sudo pvcreate /dev/nvme0n1p4
sudo vgcreate vg_k8s_nvme /dev/nvme0n1p4
```

**Why this exact order:** shrink the PV metadata before the partition, so LVM
is never "pretending" the PV is bigger than the partition. `partprobe` makes
the kernel see the new partition. We verify health immediately after.

**Verified after migration** (all intact):
- `/` ext4 98G (66G free), `/var/lib/rancher/rke2` xfs 320G (314G free) — both
  still mounted, no failed units.
- `ubuntu-vg` → 730G free
- `vg_k8s_nvme` → **754.6G fast NVMe** (was deferred, now created)

## 10.5 Enable OpenEBS-required LVM module

```bash
sudo modprobe dm_snapshot
echo dm_snapshot | sudo tee /etc/modules-load.d/openebs-lvm.conf
```

**Why:** OpenEBS LocalPV LVM needs `dm-snapshot` (device-mapper snapshot). The
file makes it load at every boot.

## Checkpoint 7 (verified on alpha)

<table>
<tr><th>Requirement</th><th>Status</th></tr>
<tr><td>root filesystem with free headroom</td><td>✅ 66G free (30% used)</td></tr>
<tr><td><code>/var/lib/rancher/rke2</code> on fast storage</td><td>✅ 320G NVMe, 314G free</td></tr>
<tr><td><code>vg_k8s_nvme</code> visible</td><td>✅ 754.6G fast NVMe</td></tr>
<tr><td><code>vg_k8s_hdd</code> visible</td><td>✅ 3.27T</td></tr>
<tr><td>meaningful emergency reserve</td><td>✅ ~2.2T unallocated on HDD</td></tr>
<tr><td><code>dm_snapshot</code> loaded + persisted</td><td>✅</td></tr>
</table>

**Infra encoding:** `infra/ansible/roles/storage/` — `defaults/main.yml`
commits the intended VG names (`rke2`, `vg_k8s_nvme`, `vg_k8s_hdd`), not device
serials; `tasks` idempotently create the rke2 LV, mount it, create the fast +
bulk VGs, and load/persist `dm_snapshot`. Both K8s VGs now exist on alpha.