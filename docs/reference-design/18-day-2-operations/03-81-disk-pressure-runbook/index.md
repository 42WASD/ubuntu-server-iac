# Disk-pressure runbook

If disk approaches critical:

First identify which filesystem:

```bash
df -hT
df -ih
sudo du -xhd1 /var | sort -h
sudo du -xhd1 /var/lib/rancher/rke2 | sort -h
journalctl --disk-usage
sudo vgs
sudo lvs
```

Do not begin with:

```bash
rm -rf /var/lib/rancher/rke2/*
```

Possible safe categories:

```text
journald retention
container image GC through runtime-supported commands
old application logs
expired build cache on build01
Harbor registry GC through Harbor
old etcd snapshots beyond retention
```

Use the owner of each data type to clean it.

---
