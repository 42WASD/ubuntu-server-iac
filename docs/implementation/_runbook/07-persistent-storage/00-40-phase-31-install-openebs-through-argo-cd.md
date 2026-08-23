---
phase: 07-persistent-storage/install-openebs-through-argo-cd
---

# Phase 31 — install OpenEBS through Argo CD

**Intent:** install the OpenEBS unified chart via Argo CD, enabling only the
LocalPV LVM engine we actually use. Do **not** deploy Mayastor (replicated
engine) on a single-node host just to imitate replication.

Reference: `docs/reference-design/07-persistent-storage/install-openebs-through-argo-cd/`

## 31.1 Design decision

This is a single-node local-storage host (control-plane + worker on `alpha`).
Replication across nodes is meaningless here, so:

```text
enable  LocalPV LVM   -> provisions nvme-fast / nvme-db / hdd-bulk (Phase 32)
disable Mayastor      -> no fake HA, no extra etcd/agents
disable ZFS / Rawfile -> not used
disable Loki + Alloy  -> we run our own monitoring stack, no second one
```

The `openebs` namespace already exists from the platform baseline
(`infra/kubernetes/platform/namespaces/platform.yaml`, label
`platform.tier: platform`). RKE2's default Pod Security Admission is
`privileged`, so the LVM driver's privileged host-device mounting is allowed.

## 31.2 Files added

- `infra/kubernetes/platform/openebs/values.yaml` — chart overrides:
  `engines.local.lvm.enabled: true`, `engines.replicated.mayastor.enabled: false`,
  zfs/rawfile disabled, `loki.enabled: false`, `alloy.enabled: false`.
- `infra/kubernetes/bootstrap/argocd/apps/platform-openebs.yaml` — multi-source
  Argo Application (project `platform`, sync-wave `-3`), chart `openebs` pinned
  to `4.5.1` from `https://openebs.github.io/openebs`, values from the repo
  `$values` ref, destination namespace `openebs`.

`platform-root` recurses `infra/kubernetes/bootstrap/argocd/apps/`, so the new
Application is picked up automatically.

## 31.3 Deploy

```bash
# hard-refresh the app-of-apps so it sees the new child Application
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# then sync platform-root once, which materialises the child app
kubectl -n argocd patch application platform-root \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"hook":{}}}}}'
# then sync the OpenEBS child app
kubectl -n argocd patch application platform-openebs \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"hook":{}}}}}'
```

## 31.4 Verified

```bash
kubectl -n argocd get application platform-openebs
kubectl get pods -n openebs
kubectl get csidriver
```

Live result:

```text
$ kubectl -n argocd get application platform-openebs
NAME               SYNC STATUS   HEALTH STATUS
platform-openebs   Synced        Healthy

$ kubectl get pods -n openebs
NAME                                                     READY   STATUS   RESTARTS   AGE
platform-openebs-localpv-provisioner-...-g2kkq            1/1     Running  0          2m
platform-openebs-lvm-localpv-controller-...-cvkgz         5/5     Running  1          2m
platform-openebs-lvm-localpv-node-...-c225c               2/2     Running  0          2m

$ kubectl get csidriver
local.csi.openebs.io   false   true   true   <unset>   false
```

The CSI driver `local.csi.openebs.io` is registered. The chart also pre-created
`openebs-hostpath` StorageClass (not used by our tenants).

### LVM engine discovered the VGs

The LVM node agent (`openebs-lvm-node`) created the LVMNode object
`openebs/alpha` and discovered all host volume groups:

```text
kubectl get lvmnodes.local.openebs.io -n openebs
NAMESPACE   NAME    AGE
openebs     alpha   89s
```

Node-agent log shows `vg_k8s_nvme`, `vg_k8s_hdd` (and the pre-existing
`ubuntu-vg`) were collected with full size/free metadata. `vg_k8s_nvme` and
`vg_k8s_hdd` are the pools that Phase 32 StorageClasses will target via
`vgpattern`.

## 31.5 Next step (Phase 31 → 32)

With the LVM engine live and the VGs discovered, Phase 32 creates the three
StorageClasses (`nvme-fast`, `nvme-db`, `hdd-bulk`) pointing at those VGs.