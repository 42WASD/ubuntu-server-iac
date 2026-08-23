# Storage reference

```text
ROOT / OS
  never build cache
  never model cache
  never registry bulk data

RKE2 DATA
  dedicated fast filesystem

vg_k8s_nvme
  OpenEBS owned
  fast PVCs

vg_k8s_hdd
  OpenEBS owned
  bulk PVCs

build01
  BuildKit cache

offsite
  disaster-recovery copies
```

---
