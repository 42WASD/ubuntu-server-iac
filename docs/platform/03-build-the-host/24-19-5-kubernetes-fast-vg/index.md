# Kubernetes fast VG

OpenEBS LocalPV LVM needs an LVM volume group.

Example desired name:

```text
vg_k8s_nvme
```

Do not manually create application LVs inside that VG.

OpenEBS owns those LVs.

Example **only after verifying the exact PV/partition**:

```bash
sudo pvcreate /dev/<NVME_K8S_PARTITION>
sudo vgcreate vg_k8s_nvme /dev/<NVME_K8S_PARTITION>
```

Check:

```bash
sudo vgs vg_k8s_nvme
```

---
