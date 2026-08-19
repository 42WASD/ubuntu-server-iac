# desired logical layout

Do not put every growing directory under `/`.

Conceptual layout:

```text
NVMe
├── EFI / boot
├── root filesystem
├── /var/log
├── /home
├── /var/lib/rancher/rke2
├── fast Kubernetes LVM VG
└── deliberately unallocated reserve

HDD
├── bulk Kubernetes LVM VG
├── model/cache area
├── local backup staging
└── deliberately unallocated reserve
```

## Why reserve free space?

Because future-you may need to extend:

```text
root
RKE2 data
home
database storage
```

LVM free extents are far more useful during an emergency than a 100%-allocated disk.

---
