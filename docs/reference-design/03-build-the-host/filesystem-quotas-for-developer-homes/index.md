# filesystem quotas for developer homes

Cgroups limit running resources.

They do not stop:

```text
alice writes 900 GB into /home/alice
```

Use filesystem user quotas where the filesystem/layout supports them.

This platform's `/` is **ext4** on LVM, mounted `usrquota` (see `scripts/system/apply-quotas.sh`, the enforced source of truth). The `/var/lib/rancher/rke2` XFS volume is mounted `noquota` — container/storage quotas are handled by Kubernetes, not kernel disk quotas.

Applied policy (GiB, set by `scripts/system/apply-quotas.sh`):

```text
owner (jyao, management account):
  soft limit:  6 GiB  (grace period: 7 days)
  hard limit: 10 GiB  (writes fail once exceeded)

normal developer:
  soft limit: 10 GiB
  hard limit: 15 GiB
```

A **soft** limit warns and starts a grace timer; a **hard** limit blocks writes
with `Disk quota exceeded`. Quotas count blocks owned by the uid anywhere on
`/`, not just `$HOME`.

## How each user sees their own usage

Users do not need `du` or `lsblk` for this — the kernel tracks it:

```bash
quota -s        # own usage vs soft/hard limits, human-readable
du -sh ~        # optional cross-check of home directory size
```

`quota -s` prints the used space, the soft/hard limits, and any grace timer
(a `*` marks being over soft). Admins see everyone at once with:

```bash
sudo repquota -s /
sudo quota -s -u <user>
```

On an XFS filesystem the equivalent is `xfs_quota -x -c 'report -h' /mount`.

Shared data belongs in explicitly-managed project storage, not in one person's home directory.

## Checkpoint 8

A test developer cannot fill the entire root or home filesystem.

---
