# fresh-install target

For a fresh reinstall, a reasonable starting design is approximately:

```text
2 TB marketed NVMe

EFI/boot                   small
root                       ~120 GiB
/var/log                    ~64 GiB
/home                       ~96 GiB
/var/lib/rancher/rke2      ~320 GiB
Kubernetes fast VG         ~800 GiB
future VM/sandbox reserve  ~300 GiB
unallocated reserve        remaining
```

And on the 6 TB HDD:

```text
bulk Kubernetes VG         ~2.5-3.0 TiB
models/cache               ~0.5 TiB
local backup staging       ~0.7-1.0 TiB
future/game/bulk reserve   remaining
```

These are **starting allocations**, not immutable truth.

---
