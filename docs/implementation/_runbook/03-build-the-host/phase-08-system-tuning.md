---
phase: 03-build-the-host/system-tuning-and-resource-safety
---

# Phase 8 — system tuning and resource safety

**Intent:** baseline kernel/logging settings that make `alpha` a safe,
predictable Kubernetes host. Each change is persisted so it survives reboots,
and each is done for an explicit reason (not "copy-paste tuning").

Config sources of truth live in `scripts/system/` and are deployed to the
standard system locations on `alpha`.

---

## 8.1 Disable swap (initially)

**Why:** Kubernetes 1.x predates stable swap support and, even when enabled,
swap makes memory accounting unpredictable and adds variables while we are
first validating the cluster. We start with swap **off** and can re-enable it
later as a deliberate feature.

```bash
# 1) Show whether swap is active
swapon --show
#    -> /swap.img   8G   0B   -1     (8G swap file, active)

# 2) Turn swap off for the running session
sudo swapoff -a

# 3) Stop it from coming back on reboot: comment the fstab entry
#    (we deliberately overwrite the line with an explanation, not just delete,
#    so the original intent stays visible in /etc/fstab)
sudo sed -i 's|^/swap.img.*|# /swap.img was disabled for initial k8s deployment (Phase 8)|' /etc/fstab
```

**Verified:**
```bash
swapon --show          # (empty) -> no swap active
grep -i swap /etc/fstab
# # /swap.img was disabled for initial k8s deployment (Phase 8)
```

---

## 8.2 inotify limits

**Why:** RKE2 runs containers that create a LOT of inotify watchers (files +
directories being watched). Ubuntu's default is only `1024` instances, which is
too low for workloads like `kubectl`/IDE auto-reload/helm/CI inside pods and
can cause "too many files open"/watcher exhaustion. We raise the per-user
limits.

```bash
# 4) Deploy the inotify sysctl drop-in (source: scripts/system/)
sudo cp 99-platform-inotify.conf /etc/sysctl.d/

# 5) Apply all sysctl settings now (also picks up network conf)
sudo sysctl --system
```

Contents of `99-platform-inotify.conf`:
```sysctl
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches   = 524288
```

> Note: `max_user_watches` was already `1048576` on alpha (>= our 524288), so
> that line was a no-op; the important change was `max_user_instances`
> `1024 -> 8192`.

---

## 8.3 Basic IP forwarding

**Why:** a Kubernetes host must forward packets to route Pod traffic between
nodes and for Cilium to move traffic. Without `ip_forward=1`, Pod networking
breaks. We only enable forwarding itself — we do NOT add a general router
(masquerading etc. stays out).

```bash
# Deploy the network sysctl drop-in (source: scripts/system/)
sudo cp 99-platform-network.conf /etc/sysctl.d/
sudo sysctl --system
```

Contents of `99-platform-network.conf`:
```sysctl
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
```

> On alpha these were already `1/1` (Ubuntu default had them on), so this was
> a confirm/no-op — but the file pins it explicitly so future reboots/config
> resets can't silently flip it off.

---

## 8.4 journald storage bound

**Why:** without a cap, the systemd journal grows unbounded and can fill the
system disk — fatal for a K8s node. We bound size + retention and enable
compression so logging can never starve the OS of space.

```bash
# Deploy the journald drop-in (source: scripts/system/)
sudo mkdir -p /etc/systemd/journald.conf.d
sudo cp 50-platform.conf /etc/systemd/journald.conf.d/

# journald only reads this at restart, so restart it
sudo systemctl restart systemd-journald
```

Contents of `50-platform.conf`:
```ini
[Journal]
SystemMaxUse=4G     # persistent journal cap
SystemKeepFree=8G   # always keep >=8G free on the system disk
RuntimeMaxUse=1G    # in-memory /run journal cap
MaxRetentionSec=14day
Compress=yes
```

**Verify:**
```bash
journalctl --disk-usage   # -> Archived and active journals take up 88M
systemctl is-active systemd-journald   # -> active
```

---

## 8.5 Full verification on alpha

```bash
swapon --show                              # (empty)
sysctl fs.inotify.max_user_instances       # 8192
sysctl fs.inotify.max_user_watches         # 524288
sysctl net.ipv4.ip_forward                 # 1
sysctl net.ipv6.conf.all.forwarding        # 1
journalctl --disk-usage                    # 88M
grep inotify /etc/sysctl.d/99-platform-inotify.conf
grep ip_forward /etc/sysctl.d/99-platform-network.conf
```

All persisted under `/etc/sysctl.d/` and `/etc/systemd/journald.conf.d/`, so
they survive reboots.

**Infra encoding:** these belong in the `base` role (host-wide sysctl +
journald). Add to `infra/ansible/roles/base/` tasks: copy `99-platform-*.conf`
to `/etc/sysctl.d/`, `50-platform.conf` to `/etc/systemd/journald.conf.d/`,
reload `sysctl`, and restart `systemd-journald`. Swap is bootstrap-time
(keep as a documented manual step / bootstrap task).

---

## 8.6 Follow-up — re-enable swap (after a host hard freeze)

**Phase:** 2026-08-26. A host **hard lockup** (kernel log simply stopped at
09:08:30 — no panic, no OOM, no shutdown) occurred while a 16-way
`dotnet publish` was writing a WASM AOT build to the **RAM-backed** `/tmp`
(tmpfs, `size=50%` = ~54G) with **swap disabled**. Root cause: heavy interactive
host-side builds writing to tmpfs, with **zero swap headroom**, exhausted
reclaimable RAM and the kernel could not make progress → hard freeze.

**Why re-enable now (deliberate decision):** the Phase 8.1 disable was meant to
be temporary — "re-enable later as a deliberate feature". The cluster is now
validated and stable. Pod memory accounting is unaffected (pods run in their
own cgroup limits; swap is a host-level safety net for interactive `dotnet`,
`make -j`, pytest, etc.). Re-enabling swap restores a pressure absorber so a
heavy build can't hard-freeze the host again.

**Commands (live, verified):**
```bash
# confirm the swap file still exists and is a valid swap
ls -lh /swap.img                      # 8.0G, valid Linux swap file (UUID kept)

# add it back to fstab so it survives reboots
echo '/swap.img none swap sw 0 0' >> /etc/fstab

# activate immediately
sudo swapon /swap.img

# verify
swapon --show                         # /swap.img  file  8G  0B  -1
systemctl list-units --type=swap --all # swap.img.swap loaded active active
free -h | grep -i swap                # Swap: 8.0Gi 0B 8.0Gi
sysctl vm.swappiness                  # 60 (default)
```

**Verified:** swap active now and persists via `/etc/fstab` + the
`swap.img.swap` unit.

**Guidance — do users write to `/tmp`?** `/tmp` on this host is a **RAM-backed
tmpfs** (size = 50% RAM), so anything written there consumes **system RAM**, not
disk. Small/transient temp files are fine. **Large build/publish outputs
belong on real disk** (`/var/tmp/`, `~/publish`, or a workspace), not `/tmp` —
that avoids the RAM-pressure path that contributed to this freeze. This is now
covered by the swap safety net, but redirecting big outputs off tmpfs is still
the correct practice.

**Infra encoding:** this is a host-bootstrap deviation from Phase 8.1. If it
becomes the permanent policy, update the `disable-swap-initially` reference
design page (mark swap re-enabled, revise rationale) and the `base` role so a
fresh rebuild keeps swap on.