---
order: 8
---

# Single server dies

Expected behavior:

```text
public web = down
Kubernetes = down
games = down
local monitoring = down
```

External status should still work.

Recovery depends on:

```text
Git
Autoinstall
Ansible
offsite etcd snapshots
offsite app data backups
documentation
```

That is why GitOps is not a substitute for backup.

---
