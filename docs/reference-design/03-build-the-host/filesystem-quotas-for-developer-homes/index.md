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
  soft limit: 10 GiB  (grace period: 7 days)
  hard limit: 15 GiB  (writes fail once exceeded)
  # Raised from 6/10 GiB on 2026-09-01: the owner hit the old 10 GiB hard
  # ceiling and writes started failing (repo dir + .cache + workspace state).

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

## The rule this implies: workloads must never run as a human UID

Quotas are keyed on **uid**, and they count *every block that uid owns anywhere
on `/`* — not just `$HOME`. That has a consequence which is easy to miss and
expensive to debug:

> **Any container running as a human UID inherits that human's quota, including
> an expired grace timer — and can then never write a single byte.**

`/var/lib/kubelet/pods/...` (where every `emptyDir` lives) is on `/`, and the
root LV is mounted `quota,usrquota`. So a pod with `runAsUser: 1000` is charged
to the human `jyao`; a pod with `runAsUser: 1001` is charged to
`jyao-42admin`. Neither is a workload identity.

### Why "grace: none" is fatal, not a warning

A soft limit alone only warns and starts a 7-day grace timer. Once that timer
**expires**, the soft limit behaves like a hard limit and *every* write by that
uid fails with `EDQUOT`:

```text
$ sudo repquota -u /
User            used    soft    hard  grace    used  soft  hard  grace
jyao-42admin +- 14203876 10485760 15728640  none   49319     0     0
                  ^^ 13.5 GiB used, 10 GiB soft, grace EXPIRED ("none")
```

A pod in this state crash-loops with an error that looks nothing like a quota
problem, because the failing write is incidental:

```text
level=fatal msg="could not write TLS certificate: write /tmp/tls.crt:
disk quota exceeded"
```

`/tmp` there is an `emptyDir` on `/`. The disk was 53% free. This is the same
class of failure as the games "bad IO" crash loop; it cost 4,961 container
restarts before being traced.

> **Diagnostic rule:** `Disk quota exceeded` is a *quota* signal, not a disk-full
> signal and not an I/O error. Check `repquota`, not `df`. Reboots do not fix it
> — the usage is persistent, and recreating an `emptyDir` frees space that was
> never the constraint.

### The convention

Every workload gets a **dedicated, non-human UID**. This platform standardises
on **10000** (out of the human range and out of the image-default range):

```yaml
spec:
  template:
    spec:
      securityContext:
        runAsUser: 10000
        runAsGroup: 10000
        fsGroup: 10000
```

Acceptable alternatives are UIDs an image already ships with and that are not
human on this host — `999`, `65532`, `65534`. Push common images (`1000`,
`1001`) are the trap: they collide with the first human accounts created by
`adduser`.

Images that re-chown their data directory on start (the `itzg/*` Minecraft
images, for example) must also be told the UID, or they will undo the pod
`securityContext`:

```yaml
env:
  - name: PUID
    value: "10000"
  - name: PGID
    value: "10000"
```

### Audit command

Run this after adding workloads, and after any reboot that shows unexplained
`CrashLoopBackOff`:

```bash
kubectl get pods -A -o json | python3 -c '
import sys, json, collections
b = collections.defaultdict(list)
for p in json.load(sys.stdin)["items"]:
    ns, nm = p["metadata"]["namespace"], p["metadata"]["name"]
    for u in {p["spec"].get("securityContext", {}).get("runAsUser"),
              p["spec"]["containers"][0].get("securityContext", {}).get("runAsUser")}:
        if u is not None:
            b[u].append(f"{ns}/{nm}")
for u in sorted(b):
    flag = "  <== HUMAN ACCOUNT" if u in (1000, 1001) else ""
    print(f"  uid {u:>6}: {len(b[u]):>2} pod(s){flag}")
'
```

Cross-check the human UIDs against this host:

```bash
getent passwd 1000 1001     # whichever names appear are OFF-LIMITS for pods
```

Results on `alpha` are recorded in the runbook
`03-build-the-host/phase-11-filesystem-quotas.md` §11.9, which also documents
the two RKE2-packaged system pods deliberately left on 1000 (vendor charts, not
in our GitOps source of truth, and they write nothing to `/`).

## Checkpoint 8

A test developer cannot fill the entire root or home filesystem.

---
