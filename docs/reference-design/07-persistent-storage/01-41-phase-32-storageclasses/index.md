# Phase 32 — StorageClasses

Prefer `vgpattern` over permanently coupling manifests to a single exact VG name if you plan to add machines later.

Example fast class:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nvme-fast
provisioner: local.csi.openebs.io

allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer

parameters:
  storage: "lvm"
  vgpattern: "vg_k8s_nvme.*"
  fsType: xfs
```

Database class:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nvme-db
provisioner: local.csi.openebs.io

allowVolumeExpansion: true
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer

parameters:
  storage: "lvm"
  vgpattern: "vg_k8s_nvme.*"
  fsType: xfs
```

Bulk class:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: hdd-bulk
provisioner: local.csi.openebs.io

allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer

parameters:
  storage: "lvm"
  vgpattern: "vg_k8s_hdd.*"
  fsType: xfs
```

Start with **thick provisioning**.

Do not add:

```yaml
thinProvision: "yes"
```

until you have thin-pool monitoring and failure procedures.

---
