---
phase: 03-build-the-host/18-18-phase-9-developer-cpu-ram-pid-limits-on-the-host
---
# Phase 9 — developer CPU/RAM/PID limits on the host

**Intent:** protect the 128-core host from runaway developer builds (pytest
`-n64`, `make -j4`, a runaway Python program, 10k child processes). We use
per-UID systemd user slices so each developer is boxed in, without them being
able to starve other users or exhaust memory.

> Layer distinction: these limits protect the HOST. K8s `ResourceQuota`
> protects a NAMESPACE; BuildKit limits protect the BUILDER. We do all three
> at their proper layers.

## 9.1 Find UIDs

```bash
for u in jyao jyao-42admin ehammoud mayan mtangalv; do echo "$u -> $(id -u $u)"; done
```
Result on alpha: `jyao=1000`, `jyao-42admin=1001`, `ehammoud=1002`,
`mayan=1003`, `mtangalv=1004`. `nproc` → **128**.

**Why UIDs matter:** systemd puts each human user in a per-UID slice named
`user-<UID>.slice`. We add drop-ins there to set the limits.

## 9.2 Deploy slice drop-ins

Source of truth: `scripts/system/50-platform-limits.{owner,normal}.conf`.

Owner (`jyao`, UID 1000) gets a larger profile; the four tenant users get the
normal-developer profile.

```bash
# owner profile -> user-1000.slice.d
sudo mkdir -p /etc/systemd/system/user-1000.slice.d
sudo cp scripts/system/50-platform-limits.owner.conf \
        /etc/systemd/system/user-1000.slice.d/50-platform-limits.conf

# normal profile -> tenant users
for uid in 1001 1002 1003 1004; do
  sudo mkdir -p /etc/systemd/system/user-$uid.slice.d
  sudo cp scripts/system/50-platform-limits.normal.conf \
          /etc/systemd/system/user-$uid.slice.d/50-platform-limits.conf
done
```

**Why these values:**
- `CPUQuota=400%` → ~4 cores for a normal dev; 800% (~8 cores) for the owner.
  On 128 cores this is generous but bounded.
- `MemoryHigh` → pressure/throttling boundary; `MemoryMax` → hard ceiling
  (OOM-kill the slice, not the host).
- `TasksMax` → process/thread ceiling (stops the 10000-fork runaway).
- `IOWeight` → lower I/O priority than default (100) services.

## 9.3 Reload + verify

```bash
sudo systemctl daemon-reload
systemctl show user-1000.slice -p CPUQuotaPerSecUSec -p MemoryHigh -p MemoryMax -p TasksMax -p IOWeight
```

**Verified on alpha** (matches intended profiles):

<table>
<thead><tr><th>Slice</th><th>CPU</th><th>MemoryHigh</th><th>MemoryMax</th><th>TasksMax</th><th>IOWeight</th></tr></thead>
<tbody>
<tr><td>user-1000 (jyao)</td><td>8s (800%)</td><td>16G</td><td>24G</td><td>8192</td><td>75</td></tr>
<tr><td>user-1001..1004</td><td>4s (400%)</td><td>8G</td><td>12G</td><td>4096</td><td>50</td></tr>
</tbody>
</table>

> NOTE: existing logged-in sessions only pick up new limits after the user
> logs out and back in (the slice is recreated at login).

---

**Infra encoding:** `infra/ansible/roles/developer_limits/` — `defaults/main.yml`
(owner/normal profiles + `developer_limits_users` list), `tasks/main.yml`
(getent UID lookup, mkdir + template drop-in), `templates/50-platform-limits.conf.j2`,
`handlers/main.yml` (daemon-reload). The drop-ins deployed manually above mirror
exactly what the role renders.