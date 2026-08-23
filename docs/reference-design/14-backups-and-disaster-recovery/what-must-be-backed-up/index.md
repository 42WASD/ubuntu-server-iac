# what must be backed up

Back up separately:

```text
Git repositories
RKE2 etcd snapshots
RKE2 server token / recovery material
database-native backups
PVC data
Harbor config/data if not easily rebuilt
game worlds
user home directories where needed
WireGuard config
Cloudflare/OpenTofu state
Ansible Vault material
critical documentation
```

Do not store:

```text
backup
+
only copy of encryption key
```

on the same physical disk.

---
