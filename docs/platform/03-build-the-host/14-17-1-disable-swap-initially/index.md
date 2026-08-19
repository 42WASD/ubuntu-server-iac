# disable swap initially

Check:

```bash
swapon --show
```

If swap exists, disable for the initial Kubernetes deployment:

```bash
sudo swapoff -a
```

Comment the swap entry in `/etc/fstab` if you intend to keep it disabled.

Why start this way?

```text
predictable memory accounting
fewer variables during first cluster validation
```

You can evaluate Kubernetes swap support later as a deliberate feature.

---
