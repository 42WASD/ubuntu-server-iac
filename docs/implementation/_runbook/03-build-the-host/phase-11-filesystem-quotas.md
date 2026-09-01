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