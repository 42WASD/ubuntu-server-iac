# existing-install path

If Ubuntu is already installed:

**Do not repartition just to make the diagram look pretty.**

First inspect:

```bash
sudo pvs
sudo vgs
sudo lvs
lsblk -f
```

If the OS already uses LVM and has VG free space:

```text
create new LVs safely from free extents
```

If not:

```text
use the separate HDD / unused partitions
or schedule a clean reinstall later
```

Do not casually shrink a live filesystem.

---
