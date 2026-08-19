# Host kernel/NVIDIA update checklist

Before reboot:

```bash
uname -r
nvidia-smi
apt list --upgradable
```

After reboot:

```bash
uname -r
nvidia-smi
systemctl --failed
kubectl get nodes
kubectl get pods -A
```

Do not assume:

```text
apt upgrade succeeded
therefore GPU driver is loaded
```

---
