---
order: 0
---

# Root filesystem fills

**Cause:**

```text
container images
logs
home directories
registry
build cache
model downloads
```

**Mitigation:**

```text
separate filesystems/VGs
user quotas
BuildKit off-host
registry storage quota
journald bound
image GC
monitoring alerts
free LVM reserve
```

---
