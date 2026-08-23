# install OpenEBS through Argo CD

Install OpenEBS using its pinned chart.

Because this is a single-node local-storage design:

```text
enable LocalPV LVM
do not deploy Mayastor merely to imitate replication
```

For the unified OpenEBS chart, disable the replicated Mayastor engine if you are not using it.

Keep:

```text
LocalPV LVM
```

---
