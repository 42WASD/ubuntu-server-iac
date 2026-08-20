# Phase 1 — inventory the actual machine

Before changing storage or networking, record reality.

Run on `alpha`:

```bash
hostnamectl
uname -a
cat /etc/os-release

lscpu
free -h

lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,FSVER,MOUNTPOINTS,MODEL,SERIAL
findmnt
df -hT
df -ih

sudo pvs
sudo vgs
sudo lvs -a -o +devices

ip -br addr
ip route
resolvectl status

lspci -nn
lspci -nn | grep -i -E 'nvidia|ethernet|network|storage|nvme'

sudo smartctl --scan
sudo nvme list 2>/dev/null || true
```

Save output:

```bash
mkdir -p ~/platform-audit
{
  hostnamectl
  uname -a
  cat /etc/os-release
  lscpu
  free -h
  lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,FSVER,MOUNTPOINTS,MODEL,SERIAL
  findmnt
  df -hT
  sudo pvs
  sudo vgs
  sudo lvs -a -o +devices
  ip -br addr
  ip route
} | tee ~/platform-audit/alpha-baseline.txt
```

## Do not guess disk names

Never assume:

```text
/dev/nvme0n1 = safe disk
/dev/sda     = HDD
```

Confirm by:

```text
MODEL
SERIAL
SIZE
current mountpoints
```

A wrong `pvcreate` destroys the wrong disk just as efficiently as a correct one.

## Checkpoint 1

You should be able to answer:

```text
Which device contains /
Which physical device is the 2 TB NVMe
Which physical device is the 6 TB HDD
Whether the OS already uses LVM
How much unallocated space exists
Which NIC is the normal LAN NIC
Whether both RTX 3090s are visible on PCIe
```

Commit the **sanitized** inventory facts, not serial numbers/secrets, to:

```text
inventory/host_vars/alpha.yml
```

Example:

```yaml
host_name: alpha
os_expected: Ubuntu 26.04 LTS

hardware:
  cpu_cores: 64
  memory_gib: 128
  gpu_count: 2

storage_plan:
  nvme_class: fast
  hdd_class: bulk
```

---
