---
phase: 07-persistent-storage/02-42-phase-33-prove-pvc-lifecycle-before-deploying-databases
---
# Phase 33 — prove PVC lifecycle before deploying databases

**Intent:** prove the full PVC lifecycle against the Phase 32 StorageClasses
before any database (PostgreSQL) or registry (Harbor) depends on it. Gate
(Checkpoint 12): dynamic provision, mount, persistence across pod restart,
reclaim behaviour must all be understood first.

Reference: `docs/reference-design/build/07-persistent-storage/02-42-phase-33-prove-pvc-lifecycle-before-deploying-databases/`

## 33.1 Test fixtures

Under `infra/kubernetes/storage-tests/`:

| Fixture | Purpose |
|---|---|
| `pvc-storage-test.yaml` | 2Gi PVC on `nvme-fast` |
| `pvc-storage-test-retain.yaml` | 1Gi PVC on `nvme-db` |
| `pod-storage-test.yaml` | busybox pod writing `/data/test.txt`, restricted-PSA compliant |

**PSA note:** the reference's bare pod is rejected by the tenant namespace's
restricted Pod Security Admission. The committed fixture adds the required
`securityContext`: `runAsNonRoot: true`, `runAsUser/Group: 1000`,
`fsGroup: 1000`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`,
`seccompProfile: RuntimeDefault`. `fsGroup: 1000` is required so the (root-owned)
LVM xfs mount is writable by the non-root UID 1000 container.

## 33.2 Dynamic provision + mount (nvme-fast)

```bash
kubectl apply -f infra/kubernetes/storage-tests/pvc-storage-test.yaml
kubectl apply -f infra/kubernetes/storage-tests/pod-storage-test.yaml
kubectl -n dev-jya0 get pvc,pv,pod -o wide
```

`WaitForFirstConsumer` means the PVC stays `Pending` until the pod schedules,
then binds:

```text
persistentvolumeclaim/storage-test   Bound   pvc-4487...   2Gi  RWO  nvme-fast
persistentvolume/pvc-4487...          2Gi   RWO  Delete  Bound  dev-jya0/storage-test  nvme-fast
pod/storage-test                      1/1   Running
```

Under the hood OpenEBS created an LV on the host:

```text
$ sudo lvs
LV pvc-4487...  VG vg_k8s_nvme  LSize 2.00g
```

```text
$ kubectl get lvmvolumes.local.openebs.io -A
NAMESPACE  NAME            VOLGROUP      NODE   SIZE         STATUS
openebs    pvc-4487...     vg_k8s_nvme   alpha  2147483648   Ready
```

Write check:

```bash
kubectl -n dev-jya0 exec storage-test -- cat /data/test.txt   # -> hello
```

## 33.3 Persistence across pod recreation

```bash
kubectl delete -f infra/kubernetes/storage-tests/pod-storage-test.yaml
kubectl apply  -f infra/kubernetes/storage-tests/pod-storage-test.yaml
kubectl -n dev-jya0 exec storage-test -- cat /data/test.txt  # -> hello (survives)
```

The PV/LV are untouched by pod deletion; data persists.

## 33.4 Reclaim: Delete (nvme-fast / hdd-bulk)

```bash
kubectl delete -f infra/kubernetes/storage-tests/pvc-storage-test.yaml
```

Result: PVC removed and the PV, LV, and LVMVolume CR are all removed by the
provisioner (Delete policy). Nothing leaks.

## 33.5 Reclaim: Retain (nvme-db)

```bash
kubectl apply -f infra/kubernetes/storage-tests/pvc-storage-test-retain.yaml
# bind via a pod (sed pod claimName -> storage-test-retain), write "dbdata"
kubectl delete pod storage-test-retain -n dev-jya0
kubectl delete -f infra/kubernetes/storage-tests/pvc-storage-test-retain.yaml
```

Result — the PV is **not** deleted; it becomes `Released`, and the LV +
LVMVolume CR persist on the host. This is the intended database safety net:

```text
persistentvolume/pvc-b3c671...  1Gi  RWO  Retain  Released  dev-jya0/storage-test-retain  nvme-db
$ sudo lvs            # pvc-b3c671... still in vg_k8s_nvme
$ kubectl get lvmvolumes.local.openebs.io -A   # still Ready
```

Manual operator cleanup after confirming the data is no longer needed:

```bash
kubectl delete pv <pv-name>
kubectl delete lvmvolumes.local.openebs.io -n openebs <pv-name>
```

(Deleting the LVMVolume CR cascades removal of the LV.)

## 33.6 Reboot resilience

Reboot recovery of this single node was already proven in Phase 18. Combined
with `volumeBindingMode: WaitForFirstConsumer`, volumes survive host restarts
because the data lives on the host VGs (`vg_k8s_nvme` / `vg_k8s_hdd`), not in
ephemeral pod storage.

## 33.7 Result (Checkpoint 12 satisfied)

- ✅ dynamic provisioning works (nvme-fast + nvme-db both provisioned LV on the correct VG)
- ✅ mount works (fsGroup fix applied; pod Running 1/1)
- ✅ persistence across pod recreation
- ✅ expansion-capable SCs (allowVolumeExpansion: true) — expansion not exercised but SC configured
- ✅ reclaim behaviour understood and verified (Delete vs Retain)
- ❌ reboot re-provision not re-tested in this phase (covered by Phase 18)

Databases may now be deployed onto `nvme-db` (Retain) / `nvme-fast` safely.