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
| Disk | Size | Role | State |
|------|------|------|-------|
| `nvme0n1` | 1.9T NVMe | OS | `ubuntu-vg` PV = whole disk, 100G root, **1.76T free** |
| `sda` | 5.5T HDD | bulk | completely unformatted |

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

## 10.4 Fast NVMe VG (deferred)

`vg_k8s_nvme` is **not** created: the NVMe's only PV (`nvme0n1p3`) fully
belongs to `ubuntu-vg`. Splitting it would require shrinking a live XFS/ext4
filesystem — explicitly forbidden by the design on an existing install.
Recorded as **deferred**; can be done at the next clean reinstall.

## 10.5 Enable OpenEBS-required LVM module

```bash
sudo modprobe dm_snapshot
echo dm_snapshot | sudo tee /etc/modules-load.d/openebs-lvm.conf
```

**Why:** OpenEBS LocalPV LVM needs `dm-snapshot` (device-mapper snapshot). The
file makes it load at every boot.

## Checkpoint 7 (verified on alpha)

| Requirement | Status |
|-------------|--------|
| root filesystem with free headroom | ✅ 66G free (30% used) |
| `/var/lib/rancher/rke2` on fast storage | ✅ 320G NVMe, 314G free |
| `vg_k8s_nvme` visible | ⏸️ deferred (needs repartition) |
| `vg_k8s_hdd` visible | ✅ 3.27T |
| meaningful emergency reserve | ✅ ~2.2T unallocated on HDD |
| `dm_snapshot` loaded + persisted | ✅ |

**Infra encoding:** `infra/ansible/roles/storage/` — `defaults/main.yml`
commits the intended VG names (`rke2`, `vg_k8s_nvme`, `vg_k8s_hdd`), not device
serials; `tasks` idempotently create the rke2 LV, mount it, create `vg_k8s_hdd`,
and load/persist `dm_snapshot`. The fast NVMe VG is intentionally absent there.