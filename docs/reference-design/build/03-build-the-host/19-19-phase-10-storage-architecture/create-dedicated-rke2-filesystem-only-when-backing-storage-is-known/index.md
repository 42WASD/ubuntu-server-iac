# create dedicated RKE2 filesystem only when backing storage is known

Example **template**, not blind command:

```bash
# DANGER: replace VG name after verifying it.
sudo lvcreate -L 320G -n rke2 <OS_VG>
sudo mkfs.xfs /dev/<OS_VG>/rke2

sudo mkdir -p /var/lib/rancher/rke2
echo '/dev/<OS_VG>/rke2 /var/lib/rancher/rke2 xfs defaults,noatime 0 2' | \
  sudo tee -a /etc/fstab

sudo mount -a
```

Validate:

```bash
findmnt /var/lib/rancher/rke2
df -hT /var/lib/rancher/rke2
```

---
