# Kubernetes bulk VG

Example:

```text
vg_k8s_hdd
```

Template:

```bash
sudo pvcreate /dev/<HDD_K8S_PARTITION>
sudo vgcreate vg_k8s_hdd /dev/<HDD_K8S_PARTITION>
```

---
