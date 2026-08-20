# required LVM module

OpenEBS LocalPV LVM requires LVM utilities and `dm-snapshot`.

Verify:

```bash
lsmod | grep dm_snapshot || true
```

Load:

```bash
sudo modprobe dm_snapshot
```

Persist:

```bash
echo dm_snapshot | sudo tee /etc/modules-load.d/openebs-lvm.conf
```

## Checkpoint 7

You must have:

```text
root filesystem with free headroom
/var/lib/rancher/rke2 on intended fast storage
vg_k8s_nvme visible
vg_k8s_hdd visible
at least one meaningful emergency reserve
```

Run:

```bash
df -hT
sudo pvs
sudo vgs
sudo lvs
```

Commit **the intended VG names**, not device serial secrets, to Ansible vars.

---
