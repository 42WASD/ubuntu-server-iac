# StorageClasses

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

## ReadWriteOnce means one *mount*, not one pod per node

This trips up almost everyone, and it is the cause of rollouts that hang
forever rather than failing loudly.

The Kubernetes access mode is named `ReadWriteOnce` but the semantics are
**`ReadWriteOnce` per node in the general case, and per *volume mount* on
node-local storage**. On OpenEBS local-LVM the volume is backed by an LVM LV
attached on exactly one node, so a **second pod cannot mount it — not even on
the same node, and not even for a moment**:

```text
MountVolume.SetUp failed for volume "pvc-f2c681c5-..." :
rpc error: code = Internal desc = verifyMount: device already mounted at
[/var/lib/kubelet/pods/4d84eea2-.../volumes/kubernetes.io~csi/pvc-f2c681c5-.../mount]
```

### Why this deadlocks a default Deployment

`RollingUpdate` is the default strategy and it is **actively wrong** for any
single-writer workload on RWO storage. With `replicas: 1` and the default
`maxUnavailable: 25%`:

```text
25% of 1 replica = 0.25  ->  rounds DOWN to 0 permitted unavailable
```

So the controller may not take the old pod down before starting the new one. The
sequence is:

```text
old pod  holds the RWO mount   (often already crash-looping)
new pod  scheduled, cannot mount  -> ContainerCreating forever
rollout  waits for new pod Ready -> Progressing forever
```

Two pods exist, **neither serves**. Nothing reports the volume conflict as the
cause unless you read the pod events — the Deployment just says `Progressing`.

### The rule

Any workload whose storage must have a single writer uses `strategy: Recreate`:

```yaml
spec:
  replicas: 1
  strategy:
    type: Recreate
  template:
    spec:
      containers:
        - name: app
          volumeMounts:
            - {name: data, mountPath: /data}
```

This covers databases (Postgres, CockroachDB, SQLite-backed apps like Dex), a
Minecraft world directory, an Elasticsearch data path — anything where two
processes must never open the same files.

Two extra points worth knowing:

- **`Recreate` implies an outage window.** That is the honest trade: for a
  single-writer volume there is no way to have zero-downtime *and* one writer.
  Accept it, and use a graceful `preStop`/`terminationGracePeriodSeconds` so the
  old process flushes before it dies.
- **Clearing `rollingUpdate` has a gotcha under GitOps.** Setting
  `strategy.type: Recreate` while a `rollingUpdate:` block lingers is rejected:

  ```text
  spec.strategy.rollingUpdate: Forbidden: may not be specified when
  strategy `type` is 'Recreate'
  ```

  Removing it is straightforward with `kubectl`, but **not** with Argo CD under
  `ServerSideApply=true`, because SSA cannot delete a field it does not own.
  The fix is the `Replace=true` sync-option annotation. The full mechanism is
  documented in the runbook
  `05-gitops-bootstrap/12-37-argo-cd-instance-config.md` ("changing an
  immutable-ish field under Server-Side Apply").

### Checking a stuck rollout

```bash
kubectl -n <ns> describe pod <new-pod> | sed -n '/Events:/,$p'
kubectl -n <ns> get rs          # two RS both DESIRED>0 = surge is stuck
```

If you see `verifyMount: device already mounted`, it is this problem — not a
scheduling, image, or resource issue. Correct the strategy; do not chase the
mount error.

---
