# filesystem quotas for developer homes

Cgroups limit running resources.

They do not stop:

```text
alice writes 900 GB into /home/alice
```

Use filesystem project/user quotas where your filesystem/layout supports them.

For XFS, mount options can include:

```text
uquota
pquota
```

For ext4, user/group quota support can be enabled as appropriate.

The exact command depends on how `/home` is formatted today.

The policy target:

```text
jya0:
  soft-ish operating target: 100-150 GB
  hard ceiling:             200 GB

normal developer:
  operating target:          20-30 GB
  hard ceiling:              40-50 GB
```

Shared data belongs in explicitly-managed project storage, not in one person's home directory.

## Checkpoint 8

A test developer cannot fill the entire root or home filesystem.

---
