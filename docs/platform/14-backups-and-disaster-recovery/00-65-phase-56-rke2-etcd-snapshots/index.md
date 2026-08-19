# Phase 56 — RKE2 etcd snapshots

RKE2 embedded etcd is the cluster-state database.

This guide configured:

```text
snapshot every 6 hours
retain 12 locally
compress snapshots
```

Check:

```bash
sudo rke2 etcd-snapshot list
```

Take manual snapshot before risky platform changes:

```bash
sudo rke2 etcd-snapshot save --name before-platform-change
```

Local snapshot only protects against some failures.

Copy snapshots off-host.

---
