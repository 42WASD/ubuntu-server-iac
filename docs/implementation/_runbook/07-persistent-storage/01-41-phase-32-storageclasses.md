---
phase: 07-persistent-storage/01-41-phase-32-storageclasses
---
# Phase 32 — StorageClasses

**Intent:** expose the OpenEBS LocalPV LVM engine (installed in Phase 31) as
three StorageClasses so tenant workloads can request NVMe-fast, NVMe-database,
or HDD-bulk volumes. Use `vgpattern` (not a hard-coded VG name) so the
manifests stay valid if we later add another machine with the same VG layout.

Reference: `docs/reference-design/build/07-persistent-storage/01-41-phase-32-storageclasses/`

## 32.1 Classes

All three use `provisioner: local.csi.openebs.io` (the LVM engine), thick
provisioning (no `thinProvision: yes`), `volumeBindingMode:
WaitForFirstConsumer` and `allowVolumeExpansion: true`.

| Class | reclaimPolicy | VG pattern | Purpose |
|---|---|---|---|
| `nvme-fast` | Delete | `vg_k8s_nvme.*` | fast general-purpose storage |
| `nvme-db`   | Retain | `vg_k8s_nvme.*` | databases (keep PV on PVC deletion) |
| `hdd-bulk`  | Delete | `vg_k8s_hdd.*` | bulk / backup storage |

`nvme-db` uses `Retain` so a database PV is not auto-wiped when its PVC is
deleted — data recovery remains possible.

## 32.2 Files added

- `infra/kubernetes/platform/storageclasses/storageclasses.yaml` — the three
  StorageClass objects.
- `infra/kubernetes/bootstrap/argocd/apps/platform-storageclasses.yaml` — Argo
  Application (project `platform`, sync-wave `-20`), path
  `infra/kubernetes/platform/storageclasses`.

`platform-root` picks it up automatically.

## 32.3 Verified

```bash
kubectl get storageclass
```

```text
NAME               PROVISIONER            RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION
hdd-bulk           local.csi.openebs.io   Delete          WaitForFirstConsumer   true
nvme-db            local.csi.openebs.io   Retain          WaitForFirstConsumer   true
nvme-fast          local.csi.openebs.io   Delete          WaitForFirstConsumer   true
openebs-hostpath   openebs.io/local       Delete          WaitForFirstConsumer   false
```

`openebs-hostpath` is the chart's pre-created default and is not used by our
tenants.

## 32.4 Next step (Phase 32 → 33)

Phase 33 proves the PVC lifecycle (provision → bind → write → delete → release)
against one of these classes before any database workload lands on them.