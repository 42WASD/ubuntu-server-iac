---
phase: 03-build-the-host/filesystem-quotas-for-developer-homes
---

# Phase 11 — filesystem quotas for developer homes

**Intent:** stop one developer from filling the entire root filesystem
(`alice writes 900 GB into /home/alice`). Cgroups (Phase 9) cap *running*
CPU/RAM/PID but do NOT cap *stored* space. Filesystem quotas give each human
user a box so no single developer can exhaust `/` (Checkpoint 8).

## 11.1 Understand the layout (what we're quota-ing)

`/home` is **NOT a separate filesystem** on `alpha` — it is a plain subdirectory
of the ext4 root LV (`/`, 98G total). So we enable **ext4 user quotas on `/`**
and cap each human UID across everything they own on the root fs.

Verified on alpha:

```bash
findmnt /            # -> /dev/mapper/ubuntu--vg-ubuntu--lv on / type ext4
df -h /              # -> 98G, 28G used, 66G free
awk -F: '$3>=1000 {print $1,$3,$6}' /etc/passwd
# jyao 1000 /home/jyao ; jyao-42admin 1001 ; ehammoud 1002 ; mayan 1003 ; mtangalv 1004
```

**Why quotas on `/` and not a dedicated `/home` mount:** the reference design's
"owner 200 GB / developer 50 GB" numbers assume `/home` is its own filesystem.
On a 98G root those numbers cannot fit. Per the design's own guidance ("the
exact command depends on how `/home` is formatted today"), we derive quotas
from the real free space.

## 11.2 Design decision (owner): management stays small

The reference gives the owner the biggest box. We override that:

- **jyao** is **MANAGEMENT-ONLY** — not developing, so it needs very little space.
- **Developers** do the real build work — they get the larger share.

Shared system storage (`/usr` 9.3G, `/var` 5.4G, `/opt` 2.4G) is **not** quota'd
but eats the same root fs — so we reserve headroom for it and only hand out a
modest slice to people.

Chosen policy (soft warning / hard ceiling):

<table>
<thead><tr><th>User</th><th>Role</th><th>Soft</th><th>Hard</th></tr></thead>
<tbody>
<tr><td>jyao</td><td>owner (management)</td><td>10 GB</td><td>15 GB</td></tr>
<tr><td>jyao-42admin, ehammoud, mayan, mtangalv</td><td>developer</td><td>10 GB</td><td>15 GB</td></tr>
</tbody>
</table>

Total hard (5 users) ≈ 75 GB; `/` has ~39 GB free at the 2026-09-01 raise —
quotas are ceilings, not reservations, so this stays safe as system usage grows.

## 11.3 Enable user quotas on the root filesystem

**Why this exact order:** persist the mount option first, then remount, then
create the quota db, then enable. `quotacheck -cum` builds `/aquota.user` (the
`-m` keeps the filesystem mounted, safe on a live root).

```bash
# 1) Persist usrquota in fstab (root line: defaults -> defaults,usrquota)
sudo sed -i '/^\/dev\/disk\/by-id\/dm-uuid.*\/ ext4 defaults 0 1/s/defaults/defaults,usrquota/' /etc/fstab

# 2) Remount / with usrquota
sudo mount -o remount,usrquota /

# 3) Build the quota database (user quotas, don't remount)
sudo quotacheck -cum /

# 4) Turn quotas on
sudo quotaon -v /
```

Verified: `findmnt -no OPTIONS /` -> `rw,relatime,quota,usrquota`; `quotaon -p /`
-> `user quota on`.

> Deprecation note: quotacheck prints "use external quota files... deprecated;
> enable the feature via tune2fs -O quota". That native feature requires
> unmounting the filesystem, which is impossible on a live `/`. The external
> /aquota.user method works fine here; the native feature can be adopted on a
> reinstall/fresh-install (Part 16).

## 11.4 Apply the per-user limits

`setquota` block limits are in **KILOBYTES** (1 block = 1 KiB), so 10 GB =
10485760 and 15 GB = 15728640.

```bash
# owner (management) — 10 / 15 GB (raised from 6/10 on 2026-09-01)
sudo setquota -u jyao 10485760 15728640 0 0 /

# each developer — 10 / 15 GB
for u in jyao-42admin ehammoud mayan mtangalv; do
  sudo setquota -u "$u" 10485760 15728640 0 0 /
done
```

> 2026-09-01 quota raise: the owner hit the old 10 GiB hard ceiling — writes
> failed (`git rm` died with "Disk quota exceeded" on the index lock). Raised
> with `sudo setquota -u jyao 10485760 15728640 0 0 /` and updated the SSOT
> (`scripts/system/apply-quotas.sh`: OWNER_SOFT_GIB=10, OWNER_HARD_GIB=15) and
> the reference doc to match. Verified: `quota -s` → 10240M soft, 15360M hard,
> no grace timer.

Verified (values match policy):

```bash
$ sudo repquota /
# jyao       -- 2843164 6291456 10485760 ...
# jyao-42admin -- 16 10485760 15728640 ...
# ehammoud   -- 16 10485760 15728640 ...
# maya       -- 24 10485760 15728640 ...
# mtangalv   -- 16 10485760 15728640 ...
```

## 11.5 Checkpoint 8 test — a developer cannot fill the root

```bash
sudo -u ehammoud bash -c 'dd if=/dev/zero of=/home/ehammoud/quota-test bs=1M count=16500'
# -> dd: IO error: Disk quota exceeded
sudo rm -f /home/ehammoud/quota-test   # cleanup
```

**Result: PASSED.** The write hit the 15 GB hard cap and was rejected; the
developer cannot fill the root or any home filesystem.

## 11.6 Per-user quota visibility (verified 2026-08-29)

Each user can see their own usage/limits without admin help — the kernel
tracks it, no `du`/`lsblk` needed:

```bash
quota -s     # run as the user: own usage vs soft/hard + grace timer
du -sh ~     # optional cross-check of home size
```

Admin view:

```bash
sudo repquota -s /          # all users at once
sudo quota -s -u ehammoud   # one user
```

Verified live on alpha:

```bash
$ sudo -u ehammoud quota -s
Disk quotas for user ehammoud (uid 1002):
     Filesystem   space   quota   limit   grace   files   quota   limit   grace
/dev/mapper/ubuntu--vg-ubuntu--lv
                    76K  10240M  15360M              19       0       0

$ sudo -u jyao quota -s
Disk quotas for user jyao (uid 1000):
     Filesystem   space   quota   limit   grace   files   quota   limit   grace
/dev/mapper/ubuntu--vg-ubuntu--lv
                 8976M*  6144M  10240M   3days   88307       0       0
```

(`*` = over soft limit, grace timer running. The `tmpfs`/kubelet
"Cannot stat/resolve" warnings on stderr are benign — quota only reports on
the ext4 root.)

Docs updated to match the applied policy (owner 6/10, dev 10/15 GiB) and to
document this workflow:
`docs/reference-design/03-build-the-host/filesystem-quotas-for-developer-homes/index.md`
(+ the mirrored section in `sources/ubuntu-26.04-rke2-platform-proper-stack.md`,
Phase 11). `scripts/system/apply-quotas.sh` header comment now states the real
limits.

---

**Infra encoding:**
- `scripts/system/apply-quotas.sh` — source-of-truth script (policy GiB -> KiB,
  idempotent: fstab usrquota, quotacheck, quotaon, setquota). Run with `sudo`.
- `infra/ansible/roles/quota/` — defaults/main.yml (owner/normal profiles in
  KiB + user list), tasks/main.yml (enable usrquota in fstab, quotacheck, quotaon,
  setquota loop), wired into `site.yml`.
- The manually-applied commands above mirror exactly what the role/script render.
---

## 11.9 Incident (2026-11-06) — argocd-dex-server crash loop = UID 1001 quota

Found during a pre-reboot audit: `argocd/argocd-dex-server` had accumulated
**4,961 restarts**. The failure was not memory, not TLS, and not the network:

```text
{"level":"fatal","msg":"could not write TLS certificate:
 write /tmp/tls.crt: disk quota exceeded","time":"2026-11-06T23:20:20Z"}
```

This is the **same class of failure** as the games "bad IO" crash loop
(Phase 8 incident recovery in the games repo), one UID over. It is worth
recording because the symptom ("disk quota exceeded") reads like a
disk-full
problem, and the disk was 53% free.

### Cause

Dex generates a self-signed TLS cert into `/tmp`, which is an **emptyDir** and
therefore lives under `/var/lib/kubelet/pods/...` on `/` — the ext4 root LV
mounted `rw,relatime,quota,usrquota`.

The upstream Argo CD manifest runs `argocd-dex-server` as **UID 1001**. On this
host UID 1001 is not a service account at all — it is a **human**:

```text
$ getent passwd 1001
jyao-42admin:x:1001:1006:...
```

And that human was over quota with the grace period expired:

```text
$ sudo repquota -u /
User            used    soft    hard  grace    used  soft  hard  grace
jyao-42admin +- 14203876 10485760 15728640  none   49319     0     0
                  ^^ 13.5 GiB used vs a 10 GiB soft limit, grace = none
```

`grace: none` is the key detail. Once the soft-limit grace expires, every
further write by that UID fails with `EDQUOT` — so Dex could never write its
TLS cert, and restart-looped forever. A reboot cannot fix this: the quota
usage is *persistent*, and `emptyDir` being recreated only frees space that was
never the problem.

The 13.5 GiB was a `42wasd-mc` clone under `/home/jyao-42admin/42wasd-mc`
(13 GiB) plus `.vscode-server` (1.1 GiB) — a developer checkout, not workload
data.

### Second instance, same bug

`security/dex` (the GitOps-managed one) was running as **UID 1000** = the
`jyao` human account, with `fsGroup: 1000`. It had not died only because
`jyao`'s own quota still had headroom (4.99M / 10.4M blocks). It was a latent
time bomb: the moment `jyao`'s quota filled, that Dex would fail identically.

### Fix

Both Dex instances moved to the dedicated workload UID **10000**:

- `argocd-dex-server` is **hand-installed** (the Argo CD bootstrap paradox), so
  it is not in Git. Patched directly:

  ```bash
  kubectl -n argocd patch deploy argocd-dex-server --type strategic -p \
    '{"spec":{"template":{"spec":{"securityContext":{"runAsUser":10000,"runAsGroup":10000,"fsGroup":10000},"containers":[{"name":"dex","securityContext":{"runAsUser":10000,"runAsGroup":10000}}]}}}}'
  ```

- `security/dex` **is** GitOps-managed, so the change went into
  `infra/kubernetes/platform/dex/deployment.yaml` (pod *and* container
  securityContext) and reaches the cluster via Argo.

The `dex-data` PVC (SQLite on `nvme-fast`, xfs, **no quota**) held
`dex.db` owned by `1000:1000`. It was re-chowned to `10000:10000` after taking
a backup:

```bash
sudo cp -p "$MOUNT/dex.db" /var/backups/dex.db.$(date +%Y%m%d-%H%M%S)
sudo chown -R 10000:10000 "$MOUNT"
```

`nvme-fast` declares no `fsGroupPolicy`, so it defaults to
`ReadWriteOnceWithFSType` and the kubelet re-chowns the volume to `fsGroup`
on mount — the manual chown made the handoff deterministic rather than relying
on that.

Verified:

```text
$ kubectl -n argocd get pod -l app.kubernetes.io/name=dex-server \
    -o jsonpath='{.items[0].spec.containers[0].securityContext.runAsUser}
                 restarts={.items[0].status.containerStatuses[0].restartCount}'
10000 restarts=0

$ kubectl -n argocd logs -l app.kubernetes.io/name=dex-server --tail=4
{"level":"info","msg":"Generating self-signed TLS certificate for this session"}
{"level":"info","msg":"dex is not configured"}
```

### Rule reinforced

**No workload may run as a human UID (1000, 1001, …).** Humans get quota
buckets with a grace period that can expire; workloads must not share that
fate. Every pod should use `runAsUser: 10000` (or an image-provided non-human
UID like 999/65532/65534).

Audit command used to find these:

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

Remaining human-UID pods after this fix:

```text
uid 1000: kube-system/rke2-metrics-server      (RKE2 Helm-managed, no writes)
uid 1000: kube-system/rke2-snapshot-controller (RKE2 Helm-managed, no writes)
```

Both are RKE2-packaged system charts that write little or nothing to `/`. They
are left alone deliberately: they are not in our GitOps source of truth, and
overriding a vendor chart's UID invites a fight on every RKE2 upgrade. If
either ever starts failing with `EDQUOT`, the fix is to drop a
`runAsUser: 10000` patch into a GitOps overlay rather than hand-editing.
