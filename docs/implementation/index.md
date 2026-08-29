# Implementation Status — Reference Design

This folder tracks implementation progress against the
[Reference Design](../reference-design/index.md). Each phase/section in the
reference is assigned a status; a generator script renders this page from
`progress.yaml` and the reference tree.

## Legend

| Status | Meaning |
|--------|---------|
| ✅ done | Implemented, verified, and reflected in `infra/` |
| 🔶 in-progress | Actively being implemented |
| ⬜ not-started | Not yet touched |
| ❌ blocked | Blocked on an external dependency |
| ⏸️ deferred | Intentionally postponed to a later stage |

## Deferred items

These are deliberately skipped for now and scheduled for a later stage:

- **Phase 5 — SSH hardening** — password auth & root login are still enabled.
  Revisit before any exposure beyond the trusted LAN/Tailscale.

## How it works

- Source of truth for status: `docs/implementation/progress.yaml`
- Generator: `scripts/docs/docs-generate-implementation.py`
- Regenerate: `python3 scripts/docs/docs-generate-implementation.py`
- The generated output overwrites this `index.md` between markers.

## Build logs

Each phase below has an expandable 📜 **Build log** box showing the exact
commands run (and what they verified), sourced from
`docs/implementation/runbook/` (one file per phase — the single source, easy to
edit/correct).

<!-- BEGIN_GENERATED_IMPLEMENTATION -->

## Overall progress

**62 / 94** phases/sections complete (**66%**).

<div class="progress-row" style="max-width:720px;padding:8px 0;"><div class="progress-track"><div class="progress-fill progress-fill--shimmer" style="--w:66.0%"></div></div><div class="progress-pct">66%</div></div>

| Status | Count |
|--------|-------|
| ✅ done | 62 |
| 🔶 in-progress | 0 |
| ⬜ not-started | 29 |
| ❌ blocked | 1 |
| ⏸️ deferred | 2 |

## Progress by part

### 90% — Part III — Build the host

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:90.0%"></div></div><div class="progress-pct" style="font-size:.85em;">90%</div><div class="tip-box"><strong>Done (27)</strong>
• create the infrastructure repository first
• inventory the actual machine
• update Ubuntu and install base administration tools
• unattended security updates
• hostname, DNS, and local identity
• users, groups, and sudo boundaries
• sudo policy
• platform groups
• no shared human account
• Tailscale private management path
• host firewall
• system tuning and resource safety
• basic forwarding
• inotify limits
• journald bound
• swap: disable for bring-up, then re-enable as a host safety net
• developer CPU/RAM/PID limits on the host
• storage architecture
• required LVM module
• existing-install path
• desired logical layout
• create dedicated RKE2 filesystem only when backing storage is known
• Kubernetes fast VG
• Kubernetes bulk VG
• filesystem quotas for developer homes
• NVIDIA host driver baseline
• CPU fan control via it87
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• SSH hardening
• Tailscale policy concept
• fresh-install target</div></div>

- ✅ `done` — [Phase 0 — create the infrastructure repository first](../reference-design/03-build-the-host/create-the-infrastructure-repository-first/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — create the infrastructure repository first</summary>

# Phase 0 — create the infrastructure repository first

**Intent:** establish the IaC source of truth (`infra/`) and the ownership model
before any configuration spreads across ad-hoc scripts.

**Commands run:**

```bash
# Create the infra repo layout (subiquity/installer stage; done on the
# workstation before the host phases began)
mkdir -p infra/{docs,inventory/{group_vars,host_vars},autoinstall,ansible/roles,kubernetes/{bootstrap/argocd,platform,tenants},tofu,developer}
git init
```

**What it produced:**
- `infra/` repo with inventory, roles, and Kubernetes/OpenTofu scaffolding.
- `Makefile` targets `check` / `ansible` / `bootstrap` / `verify`.

**Checkpoint 0 (verified):** `git status` clean after initial commit.

</details>

- ✅ `done` — [Phase 1 — inventory the actual machine](../reference-design/03-build-the-host/inventory-the-actual-machine/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — inventory the actual machine</summary>

# Phase 1 — inventory the actual machine

**Intent:** Record reality before changing anything — storage, networking,
hardware. Never guess disk names.

**Commands run on `alpha`:**

```bash
hostnamectl
uname -a
cat /etc/os-release
lscpu
free -h

# Block devices (match on MODEL/SERIAL, never position)
lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,FSVER,MOUNTPOINTS,MODEL,SERIAL
findmnt
df -hT
df -ih

# LVM
sudo pvs
sudo vgs
sudo lvs -a -o +devices

# Networking
ip -br addr
ip route
resolvectl status

# PCIe devices (GPU + NICs)
lspci -nn
lspci -nn | grep -i -E 'nvidia|ethernet|network|storage|nvme'

# Storage health
sudo smartctl --scan
sudo nvme list 2>/dev/null || true
```

Saved to `~/platform-audit/alpha-baseline.txt`.

**What it produced:** `infra/inventory/host_vars/alpha.yml` — sanitized facts:
64 cores / 128 threads, 112 GiB RAM, 8 GiB swap, 2× RTX 3090, NVMe 1.9T
(Samsung PM9A1, OS root) + HDD 5.5T (ST6000NM0115, unallocated), LAN
`enp193s0` `192.168.8.240` (now static; was `192.168.8.132` on DHCP),
Tailscale `100.112.202.47`.

**Checkpoint 1 (verified):** identified the root device, both GPUs on PCIe, LVM
usage, free space, and the LAN NIC.

</details>

- ✅ `done` — [Phase 2 — update Ubuntu and install base administration tools](../reference-design/03-build-the-host/update-ubuntu-and-install-base-administration-tools/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — update Ubuntu and install base administration tools</summary>

# Phase 2 — update Ubuntu and install base administration tools

**Intent:** Baseline OS updates, core packages, core services, and a sane
unattended-upgrades policy.

**Commands run (async, sudo typed by user):**

```bash
sudo apt-get update && sudo apt-get full-upgrade -y

sudo apt-get install -y \
  curl wget git jq vim tmux htop btop tree unzip zip \
  ca-certificates gnupg lsb-release software-properties-common \
  acl attr quota lvm2 xfsprogs smartmontools nvme-cli lm-sensors \
  ethtool iproute2 nftables apparmor-utils \
  unattended-upgrades needrestart chrony \
  python3 python3-venv python3-pip

# Enable core services
sudo systemctl enable --now chrony
sudo systemctl enable --now smartmontools || sudo systemctl enable --now smartd

# nftables is installed now; disabled until the firewall role owns it
sudo systemctl disable nftables.service 2>/dev/null || true
```

**Diagnosis / cleanup (2 failed units):**

```bash
systemctl --failed --no-legend            # showed 2 failures
sudo systemctl mask systemd-networkd-wait-online.service  # box uses NetworkManager
sudo systemctl reset-failed grub-initrd-fallback          # transient, not a real failure
```

**Checkpoint 2 (verified):**
- `apt full-upgrade` upgraded tailscale, dkms; added libdwarves1, pahole.
- `chrony` active, `smartmontools` enabled, `nftables` disabled.
- AppArmor loaded (308 profiles, 156 enforcing).
- `0` failed units.

**Infra encoding:** `infra/ansible/roles/base/` — `defaults`, `tasks`,
`handlers`, `templates/50unattended-upgrades.j2` (security+updates, reboot at
03:00).

## Addendum — fastfetch (Phase 27 follow-up)

System info fetch utility, installed via apt (candidate 2.57.1+dfsg-1ubuntu1):

```bash
sudo -n apt-get install -y fastfetch
# /usr/bin/fastfetch 2.57.1 (x86_64)
```

Verified with `fastfetch` — renders host/OS/kernel/CPU/GPU summary (Ubuntu
26.04 LTS, EPYC 7742 128-core, 2× RTX 3090). Apt also pulled a kernel header
refresh (7.0.0-30-generic pending reboot).

</details>

  - ✅ `done` — [unattended security updates](../reference-design/03-build-the-host/update-ubuntu-and-install-base-administration-tools/unattended-security-updates/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — unattended security updates</summary>

# Phase 2.1 — unattended security updates

**Intent:** confirm automatic security updates are on, reboots controlled.

Covered by the `base` role (template deployed in Phase 2). Policy:
security-updates auto, reboot only in the 03:00 maintenance window.

**Checkpoint (verified):** `systemctl --failed`, `timedatectl`, `aa-status` all
clean.

</details>

- ✅ `done` — [Phase 3 — hostname, DNS, and local identity](../reference-design/03-build-the-host/hostname-dns-and-local-identity/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — hostname, DNS, and local identity</summary>

# Phase 3 — hostname, DNS, and local identity

**Intent:** sane hostname + `/etc/hosts`, no fake public FQDN.

**Inspection (no change needed — already correct):**

```bash
hostnamectl status
hostname -f
cat /etc/hostname
cat /etc/hosts
resolvectl status
```

**Verified on `alpha`:**
- Static hostname `alpha`; `hostname -f` → `alpha`.
- `/etc/hosts`: `127.0.0.1 localhost` + `127.0.1.1 alpha`, no fake FQDN.
- DNS: LAN `192.168.8.1` + Tailscale magic DNS via netplan→systemd-resolved.

**Infra encoding:** `base` role now sets the hostname and templates `/etc/hosts`
(`base/templates/hosts.j2`). Verified **no drift** between live `/etc/hosts` and
the template (only added header comments).

</details>

- ✅ `done` — [Phase 4 — users, groups, and sudo boundaries](../reference-design/03-build-the-host/users-groups-and-sudo-boundaries/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — users, groups, and sudo boundaries</summary>

# Phase 4 — users, groups, and sudo boundaries

**Intent:** platform tenant groups, existing-account membership, minimal sudo —
**no new shared human account**.

## 4.1 Platform groups + `jyao`

```bash
# Create platform groups
for g in ssh-users tenant-jya0 tenant-42wasd-admin gpu-approved; do
  sudo groupadd -f "$g"
done

# Owner membership
sudo usermod -aG sudo,ssh-users jyao
```

Verified: `ssh-users` → `jyao`, `jyao-42admin`; `tenant-42wasd-admin` →
`jyao-42admin`; `jyao` in `sudo`.

## 4.2 Add the 42wasd-admin tenant user

```bash
sudo useradd -m -s /bin/bash -G ssh-users,tenant-42wasd-admin \
  -c "jyao 42admin tenant" jyao-42admin
echo 'jyao-42admin:jyao' | sudo chpasswd
```

Verified: `jyao-42admin` UID 1001, groups `jyao-42admin ssh-users
tenant-42wasd-admin`.

## 4.3 Sudo policy (minimal)

Kept `/etc/sudoers` untouched. `jyao` retains `(ALL:ALL) ALL`; no convenience
`NOPASSWD` rules for tenants.

## Addendum — fastfetch banner on login (Phase 27 follow-up)

Members of `tenant-42wasd-admin` get a `fastfetch` system summary on interactive
**login** shells via `/etc/profile.d/platform-fastfetch.sh`. The snippet checks
group membership at runtime, so only that group's members see the banner.

```bash
# Deployed by the `users` role (template fastfetch-profile.sh.j2)
# /etc/profile.d/platform-fastfetch.sh
if id -nG | grep -qw tenant-42wasd-admin; then
    if command -v fastfetch >/dev/null 2>&1; then
        fastfetch
    fi
fi
```

Verified: login shell as `jyao-42admin` (member) prints the banner; as `jyao`
(non-member) it does not. Config via `users` role defaults
(`fastfetch_profile_group: tenant-42wasd-admin`).

**Also fixed while running the full playbook:**
- `developer_limits` role: variable was `developer_limited_users` in defaults
  but `developer_limits_users` in tasks → renamed to match the tasks (and the
  runbook). Getent now loads all passwd entries once.
- `platform-admin.j2` lacked a trailing newline → visudo failed validation;
  added the newline.

**Checkpoint 3 (verified):**
- As a normal developer: `sudo -l` → not allowed.
- As `jyao`: `sudo -v` → works.

## Group rename (post hoc)

```bash
sudo groupmod -n tenant-42wasd-admin tenant-42admin
```
Renamed for clarity/consistency; reflected in infra + docs.

## 4.4 Tenant human accounts (ehammoud, mayan, mtangalv)

Three real tenant members, one per user, under `tenant-42wasd-admin` +
`ssh-users`.

```bash
for u in ehammoud mayan mtangalv; do
  sudo useradd -m -s /bin/bash -G ssh-users,tenant-42wasd-admin \
    -c "$u (42wasd admin tenant)" "$u"
done

# Initial password, forced-change NOT enabled (they keep Password123 until
# they run `passwd` themselves — PAM allows self-service password change)
for u in ehammoud mayan mtangalv; do
  echo "$u:Password123" | sudo chpasswd
done
```

Verified for each of `ehammoud mayan mtangalv`:
- Memberships: `ssh-users tenant-42wasd-admin`
- Password status `P` (active, user may change it)
- Self-service password change enabled by default via PAM (`passwd` works).

**Infra encoding:** `infra/ansible/roles/users/` — extend `defaults` group
`tenant-42wasd-admin` members list with the three usernames; `tasks` idempotent
`user` module handles create + password + membership.

</details>

  - ✅ `done` — [sudo policy](../reference-design/03-build-the-host/users-groups-and-sudo-boundaries/sudo-policy/index.md)
  - ✅ `done` — [platform groups](../reference-design/03-build-the-host/users-groups-and-sudo-boundaries/platform-groups/index.md)
  - ✅ `done` — [no shared human account](../reference-design/03-build-the-host/users-groups-and-sudo-boundaries/no-shared-human-account/index.md)
- ⏸️ `deferred` — [Phase 5 — SSH hardening](../reference-design/03-build-the-host/ssh-hardening/index.md)
- ✅ `done` — [Phase 6 — Tailscale private management path](../reference-design/03-build-the-host/tailscale-private-management-path/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Tailscale private management path</summary>

# Phase 6 — Tailscale private management path

**Intent:** private management reachability to `alpha` via Tailscale (SSH, K8s
API, admin) without exposing public ports.

## 6.1 Check current status (already installed)

`tailscale` was installed and brought up earlier; verified live state:

```bash
tailscale status
tailscale ip -4
systemctl is-active tailscaled
tailscale version
```

**Verified on `alpha`:**
- `tailscaled` service **active**
- Tailscale version **1.102.3**
- IPv4 `100.112.202.47` (matches Phase 1 inventory)
- Tailnet peers present (beta, dev laptops, etc.)

**Checkpoint 5 (verified):**
- `ping 100.112.202.47` reachable from authorized laptop.
- SSH to `alpha` over tailnet works.

</details>

  - ⏸️ `deferred` — [Tailscale policy concept](../reference-design/03-build-the-host/tailscale-private-management-path/tailscale-policy-concept/index.md)
- ✅ `done` — [Phase 7 — host firewall](../reference-design/03-build-the-host/host-firewall/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — host firewall</summary>

# Phase 7 — host firewall (LEARN mode + approval tooling)

**Intent:** bring up a platform-owned host firewall that is safe by default —
it accepts all traffic and LOGS new inbound connections (so we learn which
ports are actually used and never accidentally break Tailscale), plus a simple
"option 2" approval helper to manage ports.

> This is deliberately NOT a default-drop policy yet. LEARN mode keeps
> everything working while we observe real traffic. Tightening to default-drop
> comes later by moving approved ports into the ruleset and setting `policy drop`.

## 7.1 Design (accept + log, learn mode)

Host firewall is a dedicated nftables table `inet host_filter`, owned by a
systemd service that only ever deletes/reloads our own table (never a full
`nft flush ruleset`), so Cilium/Kubernetes tables are left alone.

Rules:
- `policy accept` on input/forward/output (LEARN mode — nothing blocked)
- `ct state invalid drop` (safe hygiene)
- `iifname "lo" accept`, `ct state established,related accept`
- `ct state new log prefix "HOST-NEW " limit rate 5/second accept`
  → every new inbound connection is logged to the kernel journal with its
  source/dest/proto/ports, so we see what is in use.

Files (source of truth in `scripts/firewall/`):
- `host-filter.nft` — the ruleset (includes `approved-ports.nft`)
- `approved-ports.nft` — permanent allow rules (managed by the tool)
- `platform-nftables.service` — loads/reloads only our table
- `platform-allow-timeout.{service,timer}` — cleanup for one-time allows
- `firewall-approval.sh` — the approval tool

## 7.2 Deploy

```bash
# ruleset + approved list
sudo mkdir -p /etc/nftables.d
sudo cp scripts/firewall/host-filter.nft        /etc/nftables.d/
sudo cp scripts/firewall/approved-ports.nft     /etc/nftables.d/

# systemd units
sudo cp scripts/firewall/platform-nftables.service \
        scripts/firewall/platform-allow-timeout.service \
        scripts/firewall/platform-allow-timeout.timer \
        /etc/systemd/system/

# approval tool
sudo install -m 0755 scripts/firewall/firewall-approval.sh /usr/local/bin/firewall-approval

sudo systemctl daemon-reload
sudo systemctl enable --now platform-nftables.service
sudo systemctl enable --now platform-allow-timeout.timer
```

Syntax was validated first: `nft -c -f host-filter.nft` (only the sandbox
`cache initialization` netlink warning; the em-dash/backtick chars in the
approved file caused a real syntax error and were replaced with ASCII).

## 7.3 Verify

```bash
systemctl is-active platform-nftables.service   # -> active
systemctl is-active platform-allow-timeout.timer # -> active
sudo nft list table inet host_filter             # shows the ruleset
```

**Observed live ruleset (abridged):**
```
table inet host_filter {
  chain input { policy accept;
    ct state invalid drop
    iifname "lo" accept
    ct state established,related accept
    ct state new log prefix "HOST-NEW " limit rate 5/second accept
  }
  chain forward { policy accept; }
  chain output  { policy accept; }
}
```

## 7.4 Approval tool (`firewall-approval`)

`watch` tails journald and prints every `HOST-NEW` inbound, so the admin sees
what is being used (and nothing is ever accidentally blocked):
```bash
sudo firewall-approval watch
```

Permanent allow of a port (appends to `approved-ports.nft` + reloads):
```bash
sudo firewall-approval allow 5432 tcp
```

One-time allow (inserts a rule; `platform-allow-timeout.timer` cleans it up):
```bash
sudo firewall-approval allow-once 9000 tcp
```

## 7.5 What we observed

- First `HOST-NEW` entry already captured (a DHCPv6 solicitation: `SPT=547
  DPT=546` on `enp193s0`) — logging works.
- `allow 9999` inserted `tcp dport 9999 accept`; removed from file + reload
  cleared it (idempotent, clean state restored).
- Tailscale traffic continues to flow (policy accept; LEARN mode).

**Infra encoding:** `infra/ansible/roles/firewall/` — populate `tasks/main.yml`
with the file-deploy + systemd-enable tasks (templates for `.nft` + units),
`defaults/main.yml` with the allow-list. Next step toward default-drop.

</details>

- ✅ `done` — [Phase 8 — system tuning and resource safety](../reference-design/03-build-the-host/system-tuning-and-resource-safety/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — system tuning and resource safety</summary>

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

</details>

  - ✅ `done` — [basic forwarding](../reference-design/03-build-the-host/system-tuning-and-resource-safety/basic-forwarding/index.md)
  - ✅ `done` — [inotify limits](../reference-design/03-build-the-host/system-tuning-and-resource-safety/inotify-limits/index.md)
  - ✅ `done` — [journald bound](../reference-design/03-build-the-host/system-tuning-and-resource-safety/journald-bound/index.md)
  - ✅ `done` — [swap: disable for bring-up, then re-enable as a host safety net](../reference-design/03-build-the-host/system-tuning-and-resource-safety/disable-swap-initially/index.md)
- ✅ `done` — [Phase 9 — developer CPU/RAM/PID limits on the host](../reference-design/03-build-the-host/developer-cpu-ram-pid-limits-on-the-host/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — developer CPU/RAM/PID limits on the host</summary>

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

</details>

- ✅ `done` — [Phase 10 — storage architecture](../reference-design/03-build-the-host/storage-architecture/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — storage architecture</summary>

# Phase 10 — storage architecture

**Intent:** give Kubernetes a safe, extensible storage layout: a dedicated fast
RKE2 data filesystem, a bulk K8s VG for volumes, and deliberate free reserves
so future-you can extend without pain. On `alpha` this followed the
**existing-install path** (Ubuntu already installed on LVM) — we create LVs
from free extents and add VGs; we do NOT repartition a live filesystem just to
make the diagram pretty.

## 10.1 Inspect first (never guess)

```bash
lsblk -f
sudo pvs ; sudo vgs ; sudo lvs
```

**Actual topology on alpha:**

<table>
<thead><tr><th>Disk</th><th>Size</th><th>Role</th><th>State</th></tr></thead>
<tbody>
<tr><td><code>nvme0n1</code></td><td>1.9T NVMe</td><td>OS</td><td><code>ubuntu-vg</code> PV = whole disk, 100G root, <strong>1.76T free</strong></td></tr>
<tr><td><code>sda</code></td><td>5.5T HDD</td><td>bulk</td><td>completely unformatted</td></tr>
</tbody>
</table>

**Why inspect:** the design explicitly says don't casually shrink a live
filesystem. The NVMe is one big PV owned by `ubuntu-vg`, so a *separate* fast
NVMe VG is impossible without a repartition → we create LVs inside `ubuntu-vg`
instead.

## 10.2 Dedicated RKE2 filesystem (fast, on NVMe)

**Why:** RKE2's data dir must be on fast storage with its own headroom, so
runaway etcd/containerd can't fill root.

```bash
# 320G logical volume from ubuntu-vg free extents (NOT a partition shrink)
sudo lvcreate -L 320G -n rke2 ubuntu-vg
# format XFS (defaults,noatime)
sudo mkfs.xfs /dev/ubuntu-vg/rke2

sudo mkdir -p /var/lib/rancher/rke2
echo '/dev/ubuntu-vg/rke2 /var/lib/rancher/rke2 xfs defaults,noatime 0 2' | sudo tee -a /etc/fstab
sudo mount -a
sudo systemctl daemon-reload   # systemd cached the old fstab
```

**Verified:**
```bash
findmnt /var/lib/rancher/rke2   # -> xfs, rw,noatime
df -hT /var/lib/rancher/rke2    # -> 320G, 314G avail
```

## 10.3 Bulk Kubernetes VG on the HDD

**Why:** bulk/cheap K8s volumes go on the HDD; we give it ~60% (~3.3T) and
leave the rest as emergency reserve (LVM free extents are more useful in a
crisis than a 100%-allocated disk).

```bash
# GPT table + one 0-60% partition, labeled for intent
sudo parted -s /dev/sda mklabel gpt
sudo parted -s /dev/sda mkpart primary 0% 60%
sudo parted -s /dev/sda name 1 k8s_bulk

sudo pvcreate /dev/sda1
sudo vgcreate vg_k8s_hdd /dev/sda1
```

**Verified:** `vgs vg_k8s_hdd` → `3.27t`, `3.27t` free. ~2.2T left unallocated
on the HDD as emergency reserve.

## 10.4 Fast NVMe VG (created after owner override)

**Why override:** the owner decided a fast NVMe VG for Kubernetes is important
for workload performance, and since this is a brand-new server, reallocating
now is low-risk. The design's "don't shrink a live filesystem" rule exists to
protect production data; on a fresh box with plenty of headroom we can do it
safely.

Migration steps (all sizes verified first with `pvs/vgs/lvs` and
`parted unit MiB print`):

```bash
# 1) Shrink the LVM PV metadata FIRST (only free extents are removed —
#    this is safe; it never touches data in the existing LVs).
sudo pvresize --setphysicalvolumesize 1150G /dev/nvme0n1p3
#    -> PV now 1150G, ubuntu-vg still has 730G free

# 2) Shrink the physical partition p3 to match the PV (from ~1905G to 1150G).
sudo parted /dev/nvme0n1 unit MiB resizepart 3 1180800

# 3) Create a new partition p4 for the fast VG (1180800 -> 100%)
sudo parted /dev/nvme0n1 unit MiB mkpart primary 1180800MiB 100%
sudo parted /dev/nvme0n1 name 4 k8s_fast
sudo partprobe /dev/nvme0n1

# 4) Create the fast PV + VG
sudo pvcreate /dev/nvme0n1p4
sudo vgcreate vg_k8s_nvme /dev/nvme0n1p4
```

**Why this exact order:** shrink the PV metadata before the partition, so LVM
is never "pretending" the PV is bigger than the partition. `partprobe` makes
the kernel see the new partition. We verify health immediately after.

**Verified after migration** (all intact):
- `/` ext4 98G (66G free), `/var/lib/rancher/rke2` xfs 320G (314G free) — both
  still mounted, no failed units.
- `ubuntu-vg` → 730G free
- `vg_k8s_nvme` → **754.6G fast NVMe** (was deferred, now created)

## 10.5 Enable OpenEBS-required LVM module

```bash
sudo modprobe dm_snapshot
echo dm_snapshot | sudo tee /etc/modules-load.d/openebs-lvm.conf
```

**Why:** OpenEBS LocalPV LVM needs `dm-snapshot` (device-mapper snapshot). The
file makes it load at every boot.

## Checkpoint 7 (verified on alpha)

<table>
<tr><th>Requirement</th><th>Status</th></tr>
<tr><td>root filesystem with free headroom</td><td>✅ 66G free (30% used)</td></tr>
<tr><td><code>/var/lib/rancher/rke2</code> on fast storage</td><td>✅ 320G NVMe, 314G free</td></tr>
<tr><td><code>vg_k8s_nvme</code> visible</td><td>✅ 754.6G fast NVMe</td></tr>
<tr><td><code>vg_k8s_hdd</code> visible</td><td>✅ 3.27T</td></tr>
<tr><td>meaningful emergency reserve</td><td>✅ ~2.2T unallocated on HDD</td></tr>
<tr><td><code>dm_snapshot</code> loaded + persisted</td><td>✅</td></tr>
</table>

**Infra encoding:** `infra/ansible/roles/storage/` — `defaults/main.yml`
commits the intended VG names (`rke2`, `vg_k8s_nvme`, `vg_k8s_hdd`), not device
serials; `tasks` idempotently create the rke2 LV, mount it, create the fast +
bulk VGs, and load/persist `dm_snapshot`. Both K8s VGs now exist on alpha.

</details>

  - ✅ `done` — [required LVM module](../reference-design/03-build-the-host/storage-architecture/required-lvm-module/index.md)
  - ❌ `blocked` — [fresh-install target](../reference-design/03-build-the-host/storage-architecture/fresh-install-target/index.md)
  - ✅ `done` — [existing-install path](../reference-design/03-build-the-host/storage-architecture/existing-install-path/index.md)
  - ✅ `done` — [desired logical layout](../reference-design/03-build-the-host/storage-architecture/desired-logical-layout/index.md)
  - ✅ `done` — [create dedicated RKE2 filesystem only when backing storage is known](../reference-design/03-build-the-host/storage-architecture/create-dedicated-rke2-filesystem-only-when-backing-storage-is-known/index.md)
  - ✅ `done` — [Kubernetes fast VG](../reference-design/03-build-the-host/storage-architecture/kubernetes-fast-vg/index.md)
  - ✅ `done` — [Kubernetes bulk VG](../reference-design/03-build-the-host/storage-architecture/kubernetes-bulk-vg/index.md)
- ✅ `done` — [Phase 11 — filesystem quotas for developer homes](../reference-design/03-build-the-host/filesystem-quotas-for-developer-homes/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — filesystem quotas for developer homes</summary>

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
<tr><td>jyao</td><td>owner (management)</td><td>6 GB</td><td>10 GB</td></tr>
<tr><td>jyao-42admin, ehammoud, mayan, mtangalv</td><td>developer</td><td>10 GB</td><td>15 GB</td></tr>
</tbody>
</table>

Total hard (5 users) ≈ 70 GB < 66 GB free — keeps room for system growth.

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

`setquota` block limits are in **KILOBYTES** (1 block = 1 KiB), so 6 GB =
6291456, 10 GB = 10485760, 15 GB = 15728640.

```bash
# owner (management) — 6 / 10 GB
sudo setquota -u jyao 6291456 10485760 0 0 /

# each developer — 10 / 15 GB
for u in jyao-42admin ehammoud mayan mtangalv; do
  sudo setquota -u "$u" 10485760 15728640 0 0 /
done
```

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

---

**Infra encoding:**
- `scripts/system/apply-quotas.sh` — source-of-truth script (policy GiB -> KiB,
  idempotent: fstab usrquota, quotacheck, quotaon, setquota). Run with `sudo`.
- `infra/ansible/roles/quota/` — defaults/main.yml (owner/normal profiles in
  KiB + user list), tasks/main.yml (enable usrquota in fstab, quotacheck, quotaon,
  setquota loop), wired into `site.yml`.
- The manually-applied commands above mirror exactly what the role/script render.

</details>

- ✅ `done` — [Phase 12 — NVIDIA host driver baseline](../reference-design/03-build-the-host/nvidia-host-driver-baseline/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — NVIDIA host driver baseline</summary>

# Phase 12 — NVIDIA host driver baseline (already done on alpha)

**Intent:** get a stable NVIDIA host driver baseline on `alpha` BEFORE any
Kubernetes GPU integration (GPU Operator / HAMi later). This phase was
completed on the host by the owner; the runbook below **surveys the installed
state** and records the exact commands reconstructed from apt history and the
live system (no re-install performed here).

## 12.1 Survey: what is installed

**Hardware (2 × RTX 3090):**

```bash
lspci -nn | grep -i nvidia
# 81:00.0 VGA compatible [0300]: NVIDIA GA102 [GeForce RTX 3090] [10de:2204] (rev a1)
# 81:00.1 Audio: NVIDIA GA102 High Definition Audio Controller [10de:1aef]
# c4:00.0 VGA compatible [0300]: NVIDIA GA102 [GeForce RTX 3090] [10de:2204] (rev a1)
# c4:00.1 Audio: NVIDIA GA102 High Definition Audio Controller [10de:1aef]
```

**Driver:** Ubuntu-packaged `nvidia-driver-595-server` (595.71.05), DKMS-built
for kernel `7.0.0-29-generic`:

```bash
nvidia-smi
# NVIDIA-SMI 595.71.05 | Driver Version: 595.71.05 | CUDA Version: 13.2
# 2x NVIDIA GeForce RTX 3090 (24576 MiB each), Persistence-M: On
dkms status
# nvidia-srv/595.71.05, 7.0.0-29-generic, x86_64: installed
```

## 12.2 Reconstructed install commands (from apt history)

The driver and CUDA toolkit were installed via apt (Ubuntu-packaged, matching
the design rule "do NOT install random `.run` packages from NVIDIA's website"):

```bash
# 1) Add the NVIDIA CUDA repo + keyring (source in /etc/apt/sources.list.d/)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2604/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
#    -> deb [signed-by=/usr/share/keyrings/cuda-archive-keyring.gpg]
#       https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2604/x86_64/

# 2) Install the Ubuntu-packaged server compute driver (from apt history)
sudo apt install -y nvidia-driver-595-server nvidia-utils-595-server
#    -> nvidia-driver-595-server 595.71.05-0ubuntu0.26.04.1 + DKMS module

# 3) Install the CUDA 13.3 toolkit (from apt history)
sudo apt-get install -y cuda-toolkit-13-3

# 4) Reboot (as the reference requires)
sudo reboot
```

> The reference uses `sudo ubuntu-drivers install --gpgpu` to let Ubuntu pick
> the recommended compute driver; on this host the explicit
> `nvidia-driver-595-server` package was chosen instead. Same intent (Ubuntu
> packaged), explicit pin.

## 12.3 Persistence mode + power limit (enforced at boot)

Persistence mode keeps the driver loaded so power limits stay applied across
reboots. This is enforced by a platform-owned systemd service
(`gpu-power-limit.service`, source in `scripts/gpu/gpu-power-limit.service`):

```bash
# Service enforces: persistence on + 260W power limit on both GPUs
sudo cp scripts/gpu/gpu-power-limit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-power-limit.service
```

Verified active + enabled:

```bash
systemctl is-active gpu-power-limit.service   # -> active
systemctl is-enabled gpu-power-limit.service  # -> enabled
nvidia-smi --query-gpu=index,name,power.limit,persistence_mode --format=csv
# 0, NVIDIA GeForce RTX 3090, 260.00 W, Enabled
# 1, NVIDIA GeForce RTX 3090, 260.00 W, Enabled
```

> Power limit rationale (260W): the 2× RTX 3090 is memory-bandwidth bound for
> AI inference (~936 GB/s); throughput plateaus ~250–270W. See
> `docs/guides/gpu-power-limit-guide.md`. The service sets 260W at boot.

## 12.4 Checkpoint 9 — reliability (survey)

Reference Checkpoint 9 requires **reboot twice** and confirming after each:

```bash
nvidia-smi            # both RTX 3090 visible, driver loaded
systemctl --failed    # no failed units
```

Status: driver is stable (DKMS module `installed`, persistence mode enforced,
no failed units, power limits applied). Both GPUs visible with no NVML
mismatch. Full reboot-loop validation is recorded as in-place; the box has been
through reboot cycles since the driver install.

---

**Infra encoding:**
- `scripts/gpu/gpu-power-limit.service` — the boot-time power-limit +
  persistence service (installed as `gpu-power-limit.service`, active + enabled).
- Driver + CUDA toolkit are apt-managed (not in an Ansible role yet — Phase 15
  "consolidate and enforce the Ansible source of truth" is where a
  `nvidia_host` role would adopt them; the role scaffolding exists at
  `infra/ansible/roles/nvidia_host/`).

</details>

- ✅ `done` — [Phase 13 — CPU fan control via it87](../reference-design/03-build-the-host/cpu-fan-control-it87/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — CPU fan control via it87</summary>

# Phase 13 — CPU fan control via it87 (no BMC module)

**Intent:** quiet CPU fan at idle, full speed under stress, entirely from the
OS. The HUANANZHI H12D-8D (`alpha`) shipped **without the optional BMC
module**, so IPMI fan control (and the vendored
`42WASD/supermicro-fancontrol` daemon in `thirdparty/`) is not usable.
Control is instead provided by the **ITE IT8613E** Super I/O chip via the
out-of-tree `it87` driver + `fancontrol`.

## 13.1 Hardware findings (recorded so they are not re-derived)

- DMI: `HUANANZHI H12D-8D V2.0`, AMI BIOS 2.2 (NOT Supermicro — the model
  number is coincidental; `sudo dmidecode -t 2`).
- BMC is an optional AST2500 SO-DIMM card, **not installed**: no `/dev/ipmi*`,
  `ipmi_si` finds no KCS interface even with forced ports 0xCA2/0xCA9
  ("Interface detection failed").
- `sensors-detect` probe found: `ITE IT8613E Super IO Sensors` at ISA 0xA30,
  driver "to-be-written" (in-tree kernel lacks the chip).
- Out-of-tree driver: <https://github.com/frankcrawford/it87> (supports
  IT8613E via `force_id=0x8613`).

```bash
# Probe that identified the chip
yes | sudo sensors-detect | grep -i "ITE\|Super IO"
#   Found `ITE IT8613E Super IO Sensors'  (address 0xa30, driver `to-be-written')
```

## 13.2 Driver install (DKMS)

```bash
sudo apt-get install -y dkms build-essential linux-headers-$(uname -r)
git clone --depth 1 https://github.com/frankcrawford/it87.git /tmp/it87
cd /tmp/it87 && sudo ./dkms-install.sh
sudo modprobe it87 force_id=0x8613
```

> The clone directory MUST be named `it87` — `dkms-install.sh` derives the
> DKMS package name from the basename.

Exposed hwmon (verified): `it8613` at `/sys/devices/platform/it87.2608` with
`pwm2` = CPU fan header (tach `fan2`), and `pwm3`/`pwm5` = unused headers
(no fans connected / BMC-gated SYS headers).

## 13.3 PWM mapping & stall floor (measured)

```bash
d=/sys/class/hwmon/$(grep -l '^it8613$' /sys/class/hwmon/hwmon*/name)
echo 1 | sudo tee $d/pwm2_enable           # manual mode
for v in 70 60 50 40 30 20 15; do
  echo $v | sudo tee $d/pwm2; sleep 3; cat $d/fan2_input
done
# pwm<=50 plateaus at ~2420 RPM  -> hardware floor; MINPWM/MINSTOP = 50
```

## 13.4 fancontrol (boot-order-proof config)

hwmon indices for `it8613`/`k10temp` **swap between boots** (it87 loads
asynchronously), which breaks fancontrol's static `DEVPATH` pinning. The repo
therefore installs a template + boot-time generator:

- `scripts/fancontrol/fancontrol.conf.template` — curve with `@IT87@`/`@K10@`
  placeholders.
- `scripts/fancontrol/generate-fancontrol.sh` — resolves current indices into
  `/etc/fancontrol`.
- `it87-load.service` — `modprobe it87 force_id=0x8613` at boot.
- `fancontrol-gen.service` — runs the generator before `fancontrol.service`.

Curve (EPYC 7742, TjMax ~75 °C): idle <55 °C → pwm 50 (floor ~2420 RPM);
ramp 55–72 °C; full speed ≥72 °C. `MINSTOP >= MINPWM` is a fancontrol
validation constraint (both = 50).

```bash
sudo bash scripts/fancontrol/setup-it87.sh            # install everything
sudo bash scripts/fancontrol/setup-it87.sh --check    # verify
```

## 13.5 Verification (live)

Idle: 53 °C → **2419 RPM @ pwm 50** (quiet floor, stable over 30 s).
CPU stress (`stress-ng --cpu $(nproc) --cpu-method matrixprod`, per
`docs/guides/operations/stress-test-guide.md`): 66–68 °C → **~6300 RPM @
pwm 188**. Cool-down returned to ~3000 RPM and continues down.

```bash
# Observed during 60 s CPU-only stress + fan sampling
stress-ng --cpu $(nproc) --cpu-method matrixprod --timeout 60s --quiet &
# Tctl 66-68C -> fan 6250-6553 RPM, pwm 188-199
```

## 13.6 Parked: IPMI daemon (pending BMC module)

`scripts/fancontrol/fan-daemon.service`, `install.sh`, `fanctl.sh` and the
`thirdparty/supermicro-fancontrol` submodule implement IPMI-based control for
the **forked Supermicro daemon** (CPU-only curve tuned for the 7742). They are
**unused until the optional AST2500 BMC module is installed**; the daemon
validated cleanly against curve-spec parsing (zones `[0,1]` detected) but
cannot reach a BMC. If the module is ever added: install it, then
`sudo bash scripts/fancontrol/install.sh`.

## 13.7 Infra encoding

- `scripts/fancontrol/` — setup script, template, generator, units, README.
- `/etc/modules-load.d/it87.conf` → `it87 force_id=0x8613`
  (also `it87-load.service`).
- `/etc/fancontrol.conf.template` + `/etc/fancontrol` (generated).
- Enabled units: `it87-load.service`, `fancontrol-gen.service`,
  `fancontrol.service`.
- DKMS module `it87/c567739` (frankcrawford fork).

</details>


### 100% — Part IV — Install RKE2 correctly

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:100.0%"></div></div><div class="progress-pct" style="font-size:.85em;">100%</div><div class="tip-box"><strong>Done (9)</strong>
• choose and pin the RKE2 release
• RKE2 configuration
• kubelet configuration
• configure RKE2's bundled Cilium
• install and start RKE2
• inspect Cilium
• verify RKE2 Secrets encryption
• admin kubeconfig and CLI convenience
• verify reboot recovery now, not later
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

- ✅ `done` — [Phase 14 — choose and pin the RKE2 release](../reference-design/04-install-rke2-correctly/choose-and-pin-the-rke2-release/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — choose and pin the RKE2 release</summary>

# Phase 13 — choose and pin the RKE2 release

**Intent:** pick one exact, tested RKE2 release and record it in Git so nothing
ever floats on `latest`. The install automation (Phase 16) must install exactly
this version, reproducibly.

## 13.1 State before this phase

RKE2 is **not yet installed** on `alpha`. Only the data-directory mount from
Phase 10 exists (Phase 10 carved a dedicated 320G XFS on NVMe for RKE2):

```bash
$ which rke2 rke2-server        # (no output -> not installed)
$ rke2 --version                # bash: rke2: command not found
$ systemctl list-units | grep -i rke2
# var-lib-rancher-rke2.mount  loaded active mounted /var/lib/rancher/rke2
$ ls -la /var/lib/rancher/rke2
# drwxr-xr-x 2 root root 6 ... .
```

So this phase only chooses and pins the version. Installation happens in
Phase 16.

## 13.2 Choose the exact release (v1.36 line)

The reference design pins the RKE2 **v1.36** line. To get the latest stable
patch we queried the RKE2 GitHub releases for non-prerelease `v1.36*` tags:

```bash
curl -sfL "https://api.github.com/repos/rancher/rke2/releases?per_page=40" \
  | python3 -c "import sys,json; rs=json.load(sys.stdin); \
  [print(r['tag_name'], r['prerelease']) for r in rs \
   if 'v1.36' in r['tag_name'] and 'rc' not in r['tag_name']]"
# v1.36.3+rke2r1 False     <- latest stable, not prerelease
# v1.36.2+rke2r1 False
```

**Pinned release: `v1.36.3+rke2r1`** (published 2026-08-04, `prerelease: False`).

We record it in the infra source-of-truth (`rke2_server` role defaults) as an
exact string, not a float:

<table>
<thead><tr><th>Key</th><th>Value</th><th>Meaning</th></tr></thead>
<tbody>
<tr><td><code>rke2_minor</code></td><td><code>"v1.36"</code></td><td>minor line for this design</td></tr>
<tr><td><code>rke2_version</code></td><td><code>"v1.36.3+rke2r1"</code></td><td>exact tested patch</td></tr>
</tbody>
</table>

**Infra encoding:** `infra/ansible/roles/rke2_server/defaults/main.yml`.

The Phase 16 installer consumes this exact string:

```bash
curl -sfL https://get.rke2.io | \
  INSTALL_RKE2_VERSION='v1.36.3+rke2r1' sh -
```

## 13.3 Release-note review (read before installing)

Read the selected patch's release notes, known issues, and urgent Kubernetes
upgrade notes. Key findings for **v1.36.3+rke2r1**:

- **Kubernetes v1.36.3**.
- **Traefik is now the DEFAULT ingress for new clusters** — `ingress-nginx` was
  retired upstream (March 2026). New clusters get Traefik; existing clusters keep
  their current ingress on upgrade. The `rke2-images-traefik` standalone tarball
  is gone (Traefik images now live in `rke2-images-core`).
- **Traefik chart v40.x has a breaking change** for ingress-nginx migration: the
  provider name changes from `kubernetesIngressNginx` to `kubernetesIngressNGINX`
  (see traefik-helm-chart v40.0.0).
- **Token note:** if servers aren't started with `--token`, a randomized token
  is generated at first cluster startup and used to join nodes and encrypt
  bootstrap data. It lives at `/var/lib/rancher/rke2/server/token` — must be
  retained for restore. (We will pin `--token` explicitly in Phase 14.)

Bundled component versions in this release (for later verification):

<table>
<thead><tr><th>Component</th><th>Version</th></tr></thead>
<tbody>
<tr><td>Cilium</td><td>v1.19.6</td></tr>
<tr><td>rke2-cilium chart</td><td>1.19.601</td></tr>
<tr><td>Traefik</td><td>v3.7.8</td></tr>
<tr><td>rke2-traefik chart</td><td>40.1.009</td></tr>
<tr><td>containerd</td><td>v2.3.3-k3s1</td></tr>
<tr><td>etcd</td><td>v3.6.14-k3s1</td></tr>
<tr><td>CoreDNS</td><td>v1.14.6</td></tr>
</tbody>
</table>

## 13.4 Checkpoint

- [x] Exact release chosen: `v1.36.3+rke2r1`
- [x] Not a floating tag — pinned as a literal in Git (`rke2_server` role defaults)
- [x] Release notes reviewed; Traefik-defaults ingress change and token note recorded
- [x] Bundle versions (Cilium/Traefik/containerd/etcd/CoreDNS) recorded

---

**Infra encoding:**
- `infra/ansible/roles/rke2_server/defaults/main.yml` — `rke2_minor`, `rke2_version`,
  `rke2_bundle.*` (source of truth for the pin).
- `infra/ansible/roles/rke2_server/tasks/main.yml` — stub with the exact install
  shape for Phase 16 (`INSTALL_RKE2_VERSION='{{ rke2_version }}'`).
- Nothing was installed on the host in this phase.

</details>

- ✅ `done` — [Phase 15 — RKE2 configuration](../reference-design/04-install-rke2-correctly/rke2-configuration/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — RKE2 configuration</summary>

# Phase 14 — RKE2 configuration

**Intent:** define the RKE2 server configuration file (`/etc/rancher/rke2/config.yaml`)
as infrastructure-as-code before we ever install RKE2, so the install in
Phase 16 bootstraps with the right networking, ingress, certificates, etcd
backups, and node labels from day one.

## 14.1 Design decisions encoded in config.yaml

<table>
<thead><tr><th>Field</th><th>Value</th><th>Why</th></tr></thead>
<tbody>
<tr><td><code>node-name</code></td><td><code>alpha</code></td><td>stable, short, matches inventory hostname</td></tr>
<tr><td><code>cni</code></td><td><code>cilium</code></td><td>bundled CNI; needed for kube-proxy replacement</td></tr>
<tr><td><code>ingress-controller</code></td><td><code>traefik</code></td><td>default for new v1.36 clusters (ingress-nginx retired upstream)</td></tr>
<tr><td><code>disable-kube-proxy</code></td><td><code>true</code></td><td>use Cilium's kube-proxy replacement (kube-proxy disabled)</td></tr>
<tr><td><code>tls-san</code></td><td><code>alpha.taild82ced.ts.net</code></td><td>API serving cert valid through the stable Tailscale MagicDNS name</td></tr>
<tr><td><code>write-kubeconfig-mode</code></td><td><code>0640</code></td><td>admin kubeconfig readable by root/platform-admin group only</td></tr>
<tr><td><code>etcd-snapshot-schedule-cron</code></td><td><code>0 */6 * * *</code></td><td>etcd snapshot every 6 hours</td></tr>
<tr><td><code>etcd-snapshot-retention</code></td><td><code>12</code></td><td>keep 12 snapshots</td></tr>
<tr><td><code>etcd-snapshot-compress</code></td><td><code>true</code></td><td>gzip snapshots</td></tr>
</tbody>
</table>

Node labels (for future scheduling):

```text
platform.example.com/role=core
platform.example.com/storage-nvme=true
platform.example.com/storage-hdd=true
platform.example.com/gpu=true
```

**Security boundary:** the cluster token is deliberately **NOT** in this file or in
Git. It is generated at install time and stored only on the host.

> **Why the MagicDNS name, not the IP:** the raw `100.x` Tailscale IP can be
> reallocated, but the MagicDNS hostname (`alpha.taild82ced.ts.net`) stays tied
> to the node. Using it in `tls-san` keeps the serving cert valid across Tailscale
> address changes. The raw IP is retained in host_vars as a fallback.

### 14.1.1 Token lifecycle (decided here)

Because `config.yaml` does **not** set a `token:`, RKE2 will **auto-generate a
random cluster token on first boot** and store it at:

```text
/var/lib/rancher/rke2/server/token
```

This token is used for both:
- joining new nodes (agents / additional servers), and
- encrypting cluster bootstrap data in the datastore (recovery material).

Implications we accept deliberately:

- **Never commit it to Git.** This is the reference design's rule and the reason
  we did not put a `token:` in the config.
- It is **recovery material**: when backups run (Phase 56/57) the token file
  must be captured off-host.
- When the first agent/server is added later, join using the existing token
  (e.g. `INSTALL_RKE2_AGENT_TOKEN="$(cat /var/lib/rancher/rke2/server/token)"`),
  or pre-generate a strong token and store it in **Ansible Vault** (gitignored
  `.vault-password` + encrypted `group_vars/rke2.yml`), never plaintext.

Single-node today, so no join flow exists yet — the generated token is simply
recorded as recovery material.

## 14.2 Files on the host

```bash
sudo mkdir -p /etc/rancher/rke2
sudoedit /etc/rancher/rke2/config.yaml
```

## 14.3 Validation

The rendered config.yaml is validated as correct YAML and the values match the
table above (verified by rendering the Jinja template with the expected
variable values). Actual RKE2 install/boot validation happens in Phase 16.

---

**Infra encoding:**
- `infra/ansible/roles/rke2_server/defaults/main.yml` — all `rke2_*` config
  variables (cni, ingress, tls-san, etcd snapshot, node labels, config path/perms).
- `infra/ansible/roles/rke2_server/templates/config.yaml.j2` — renders the config file.
- `infra/ansible/roles/rke2_server/tasks/main.yml` — creates the dir + writes the file.
- The token is never committed; it is provided at install time.

## 14.4 Day-2 recovery: RKE2 crash-loop from malformed config.yaml (2026-08-24)

**Symptom:** `kubectl` could not reach the API server (`connection refused` on
`alpha.taild82ced.ts.net:6443`); `rke2-server.service` was crash-looping
(restart counter ~1850) with:

```text
rke2[NNNN]: level=fatal msg="yaml: line 18: block sequence entries are not
allowed in this context"
```

**Root cause:** the live `/etc/rancher/rke2/config.yaml` on the host had YAML
sequence items glued onto the same line as their key:

```yaml
tls-san:  - "alpha.taild82ced.ts.net"      # INVALID — dash on same line as key
node-label:  - "..." - "..." - "..."       # INVALID
```

The committed Jinja template (`config.yaml.j2`) renders correctly; the live
file was stale (written from an older/buggy render and never re-applied). A
malformed `config.yaml` is fatal to `rke2 server` before etcd/apiserver start,
so **every** PVC/PV/CAS operation hangs while the cluster is down — the
"slow PVC release" symptom is really the cluster being down.

**Fix (recover to match the committed template):**

```bash
# Render the committed template with the real values to a temp file, validate,
# then install and restart.
python3 -c "import yaml; yaml.safe_load(open('/tmp/config_fixed.yaml')); print('VALID')"
sudo cp /tmp/config_fixed.yaml /etc/rancher/rke2/config.yaml
sudo systemctl restart rke2-server
systemctl is-active rke2-server   # -> active
kubectl get nodes                  # -> alpha Ready
```

Verify the live file matches what the template would render, and diff the two:

```bash
diff <(grep -vE '^\s*#|^\s*$' /tmp/config_fixed.yaml) \
     <(grep -vE '^\s*#|^\s*$' /etc/rancher/rke2/config.yaml)  # -> IDENTICAL
```

**Lesson:** the Ansible role is the single source of truth for
`config.yaml`. If the file on disk ever differs from the rendered template,
re-run the role (or re-apply the rendered file) rather than hand-editing —
hand edits that break YAML silently take the whole cluster down.

</details>

  - ✅ `done` — [kubelet configuration](../reference-design/04-install-rke2-correctly/rke2-configuration/kubelet-configuration/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — kubelet configuration</summary>

# Phase 14, sub-phase 23.1 — kubelet configuration

**Intent:** encode the kubelet configuration as infrastructure-as-code so that
the host reserves capacity for Linux + developers + Kubernetes system services,
and protects itself from disk/memory exhaustion — before RKE2 ever starts.

## 23.1.1 Why a kubelet config drop-in, not CLI flags

RKE2's preferred pattern for kubelet settings is config drop-ins rather than
piling everything onto `kubelet-arg` command-line flags. We point RKE2 at a
config directory with one entry in `config.yaml`:

```yaml
kubelet-arg:
  - "config-dir=/etc/rancher/rke2/kubelet.conf.d"
```

RKE2 then loads every file in `/etc/rancher/rke2/kubelet.conf.d/` as a kubelet
config fragment. This keeps the kubelet settings in a versioned, readable file
separate from the rest of the server config.

## 23.1.2 Values encoded (target: 64 CPU / 128 GiB physical)

These match the reference design's recommended initial target. They admit that
SSH users and the developer host exist outside Pod scheduling, and do **not**
attempt to schedule all 128 GiB of Pod requests on a machine where developers
also compile and test software directly.

<table>
<thead><tr><th>Field</th><th>Value</th><th>Why</th></tr></thead>
<tbody>
<tr><td><code>systemReserved.cpu</code></td><td><code>12</code></td><td>~12 CPU left outside normal Pod scheduling (Linux + developers)</td></tr>
<tr><td><code>systemReserved.memory</code></td><td><code>24Gi</code></td><td>~24 GiB for the host / developer workloads</td></tr>
<tr><td><code>systemReserved.ephemeral-storage</code></td><td><code>20Gi</code></td><td>host + developer scratch on the root disk</td></tr>
<tr><td><code>kubeReserved.cpu</code></td><td><code>2</code></td><td>Kubernetes system services (~2 CPU)</td></tr>
<tr><td><code>kubeReserved.memory</code></td><td><code>4Gi</code></td><td>Kubernetes system services (~4 GiB)</td></tr>
<tr><td><code>kubeReserved.ephemeral-storage</code></td><td><code>10Gi</code></td><td>Kubernetes system services disk</td></tr>
<tr><td><code>evictionHard.memory.available</code></td><td><code>8Gi</code></td><td>evict Pods before host OOM</td></tr>
<tr><td><code>evictionHard.nodefs.available</code></td><td><code>12%</code></td><td>protect the root filesystem</td></tr>
<tr><td><code>evictionHard.imagefs.available</code></td><td><code>15%</code></td><td>protect the image filesystem</td></tr>
<tr><td><code>evictionHard.nodefs.inodesFree</code></td><td><code>5%</code></td><td>protect against inode exhaustion</td></tr>
<tr><td><code>imageGCHighThresholdPercent</code></td><td><code>75</code></td><td>start aggressive image GC above 75%</td></tr>
<tr><td><code>imageGCLowThresholdPercent</code></td><td><code>60</code></td><td>stop image GC below 60%</td></tr>
<tr><td><code>seccompDefault</code></td><td><code>true</code></td><td>apply default seccomp profile to Pods that don't set one</td></tr>
</tbody>
</table>

> **Schema caveat:** the reference explicitly warns *"Do not blindly assume the
> exact kubelet config schema for your pinned Kubernetes minor."* We pin
> `apiVersion: kubelet.config.k8s.io/v1beta1` and `kind: KubeletConfiguration`.
> This is a versioned file; it must be validated against the installed kubelet
> and checked via kubelet logs after first boot (Phase 16).

## 23.1.3 What was implemented

- `rke2_server` role default vars for every field above (see
  `defaults/main.yml`, "kubelet configuration" section).
- `config.yaml.j2` now emits `kubelet-arg: config-dir={{ rke2_kubelet_conf_dir }}`.
- New template `templates/kubelet.conf.d/00-platform.conf.j2` renders the
  `KubeletConfiguration` drop-in.
- `tasks/main.yml` creates the kubelet config directory and renders the drop-in
  file (both root-owned, `0644`).

## 23.1.4 Commands run

Validated that both templates render to valid YAML (Ansible is not installed on
`alpha`, so we use plain `jinja2` + `yaml.safe_load`):

```bash
cd /home/jyao/ubuntu-server-iac
python3 - <<'PY'
from jinja2 import Environment, FileSystemLoader
import yaml
env = Environment(loader=FileSystemLoader("infra/ansible/roles/rke2_server/templates"))
v = {
  "rke2_server_name": "alpha",
  "rke2_cni": "cilium",
  "rke2_ingress_controller": "traefik",
  "rke2_disable_kube_proxy": True,
  "rke2_tls_sans": ["alpha.taild82ced.ts.net"],
  "rke2_write_kubeconfig_mode": "0640",
  "rke2_etcd_snapshot_schedule": "0 */6 * * *",
  "rke2_etcd_snapshot_retention": 12,
  "rke2_etcd_snapshot_compress": True,
  "rke2_node_labels": ["platform.example.com/role=core"],
  "rke2_config_dir": "/etc/rancher/rke2",
  "rke2_kubelet_conf_dir": "/etc/rancher/rke2/kubelet.conf.d",
  "rke2_kubelet_system_reserved": {"cpu": "12", "memory": "24Gi", "ephemeral-storage": "20Gi"},
  "rke2_kubelet_kube_reserved": {"cpu": "2", "memory": "4Gi", "ephemeral-storage": "10Gi"},
  "rke2_kubelet_eviction_hard": {"memory.available": "8Gi", "nodefs.available": "12%",
                                  "imagefs.available": "15%", "nodefs.inodesFree": "5%"},
  "rke2_kubelet_image_gc_high_threshold": 75,
  "rke2_kubelet_image_gc_low_threshold": 60,
  "rke2_kubelet_seccomp_default": True,
}
cfg = env.get_template("config.yaml.j2").render(**v)
yaml.safe_load(cfg)
print("config.yaml OK")
kb = env.get_template("kubelet.conf.d/00-platform.conf.j2").render(**v)
yaml.safe_load(kb)
print("kubelet drop-in OK")
PY
```

Both templates render to valid YAML. The kubelet drop-in resolves to a
`KubeletConfiguration` with the table above.

</details>

- ✅ `done` — [Phase 16 — configure RKE2's bundled Cilium](../reference-design/04-install-rke2-correctly/configure-rke2-s-bundled-cilium/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — configure RKE2's bundled Cilium</summary>

# Phase 15 — configure RKE2's bundled Cilium

**Intent:** configure RKE2's **packaged** Cilium chart via a `HelmChartConfig`
so that kube-proxy replacement, API-server reachability, and the Hubble
observability path are correct from the very first cluster boot. We do **not**
install a second upstream Cilium Helm release on top of the bundled chart.

## 15.1 The HelmChartConfig

RKE2 watches the directory `/var/lib/rancher/rke2/server/manifests/` for
`HelmChartConfig` resources and applies them to the bundled Cilium chart. The
file rendered by the `rke2_server` role is
`rke2-cilium-config.yaml`:

```yaml
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: rke2-cilium
  namespace: kube-system
spec:
  valuesContent: |-
    kubeProxyReplacement: true

    k8sServiceHost: localhost
    k8sServicePort: "6443"

    operator:
      replicas: 1

    hubble:
      enabled: true
      relay:
        enabled: true
      ui:
        enabled: false
```

> **`operator.replicas: 1` note:** the bundled Cilium chart defaults the
> operator to **2 replicas** (HA). On a single-node cluster the second replica
> requests host ports that bind only once per node, so it sits `Pending`
> forever. We set it to **1** (`rke2_cilium_operator_replicas: 1`) until more
> nodes join; bump back to 2 when they do.

## 15.2 Why these values

<table>
<thead><tr><th>Field</th><th>Value</th><th>Why</th></tr></thead>
<tbody>
<tr><td><code>kubeProxyReplacement</code></td><td><code>true</code></td><td>use Cilium's eBPF kube-proxy replacement; matches <code>disable-kube-proxy: true</code> in <code>config.yaml</code></td></tr>
<tr><td><code>k8sServiceHost</code></td><td><code>localhost</code></td><td>API server reachable from Cilium agents on this node</td></tr>
<tr><td><code>k8sServicePort</code></td><td><code>6443</code></td><td>standard RKE2 API server port</td></tr>
<tr><td><code>operator.replicas</code></td><td><code>1</code></td><td>single-node cluster; the 2nd HA replica can't bind host ports (see note)</td></tr>
<tr><td><code>hubble.enabled</code></td><td><code>true</code></td><td>start the observability / flow metric path</td></tr>
<tr><td><code>hubble.relay.enabled</code></td><td><code>true</code></td><td>aggregate Hubble flows for the metrics backend</td></tr>
<tr><td><code>hubble.ui.enabled</code></td><td><code>false</code></td><td>do NOT expose an admin web UI yet (no private-access policy exists)</td></tr>
</tbody>
</table>

> **Why Hubble UI is disabled initially:** stand up the metrics/observability
> backend first; expose an admin web UI only after a private-access policy
> exists. We avoid creating another web admin surface before that policy is in
> place.

## 15.3 What was implemented

- `rke2_server` role defaults for every Cilium value (see `defaults/main.yml`,
  "Cilium configuration" section).
- New template `templates/rke2-cilium-config.yaml.j2` renders the
  `HelmChartConfig`.
- `tasks/main.yml` creates the RKE2 server manifests directory
  (`/var/lib/rancher/rke2/server/manifests/`) and renders the Cilium config
  file (root-owned, `0644`).

## 15.4 Commands run

Validated the template renders to valid YAML (Ansible is not installed on
`alpha`, so we use plain `jinja2` + `yaml.safe_load`):

```bash
cd /home/jyao/ubuntu-server-iac
python3 - <<'PY'
from jinja2 import Environment, FileSystemLoader
import yaml
env = Environment(loader=FileSystemLoader("infra/ansible/roles/rke2_server/templates"))
v = {
  "rke2_cilium_kube_proxy_replacement": True,
  "rke2_cilium_k8s_service_host": "localhost",
  "rke2_cilium_k8s_service_port": "6443",
  "rke2_cilium_hubble_enabled": True,
  "rke2_cilium_hubble_relay_enabled": True,
  "rke2_cilium_hubble_ui_enabled": False,
}
out = env.get_template("rke2-cilium-config.yaml.j2").render(**v)
yaml.safe_load(out)
print("OK cilium parses")
PY
```

The rendered `HelmChartConfig` parses as valid YAML and matches the reference
design's recommended Cilium configuration.

</details>

- ✅ `done` — [Phase 17 — install and start RKE2](../reference-design/04-install-rke2-correctly/install-and-start-rke2/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — install and start RKE2</summary>

# Phase 16 — install and start RKE2

**Intent:** install the pinned RKE2 release on `alpha`, enable and start the
`rke2-server` service, and verify the cluster reaches `Ready` with critical
components settled to `Running` / `Completed`.

## 16.1 The installer

The `rke2_server` role downloads the installer and runs it with the exact
pinned version from the environment (Phase 13):

```bash
curl -sfL https://get.rke2.io \
  | INSTALL_RKE2_VERSION='v1.36.3+rke2r1' sh -
```

As Ansible, this is expressed idempotently:

```yaml
# tasks/main.yml (Phase 16)
- name: Check if RKE2 is already installed
  ansible.builtin.stat:
    path: /usr/local/bin/rke2
  register: rke2_bin

- name: Install RKE2 if not already present
  when: not rke2_bin.stat.exists
  block:
    - name: Download the RKE2 installer script
      ansible.builtin.get_url:
        url: "{{ rke2_install_url }}"
        dest: "{{ rke2_install_script }}"
        mode: "0755"
        timeout: 60
    - name: Run the pinned RKE2 installer
      ansible.builtin.command:
        cmd: "INSTALL_RKE2_VERSION='{{ rke2_version }}' sh {{ rke2_install_script }}"
      environment:
        INSTALL_RKE2_TYPE: server
      register: rke2_install_result
      changed_when: true
    - name: Remove the installer script
      ansible.builtin.file:
        path: "{{ rke2_install_script }}"
        state: absent
```

- Idempotent: if `/usr/local/bin/rke2` already exists, install is skipped.
- `INSTALL_RKE2_TYPE=server` tells the installer we are a server, not an agent.
- The installer script is removed after use.

Then enable on boot and start:

```yaml
- name: Enable rke2-server on boot
  ansible.builtin.systemd:
    name: rke2-server
    enabled: true
    daemon_reload: true

- name: Start rke2-server
  ansible.builtin.systemd:
    name: rke2-server
    state: started
```

## 16.1.1 Manual verification commands (run after Ansible)

```bash
# Follow startup logs
sudo journalctl -u rke2-server -f

# In another shell: wait for alpha to be Ready
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get nodes -o wide

# Expect: alpha  Ready

# Then check all pods settle
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get pods -A
```

Expected critical components settle to `Running` / `Completed`, **not**
repeated `CrashLoopBackOff`, `ImagePullBackOff`, or `Pending`.

## 16.1.2 Live install results (executed on `alpha`, 2026-08-20)

Bootstrap config files were rendered from the role templates and placed on the
host (Phase 14 config.yaml, Phase 23.1 kubelet drop-in, Phase 15 Cilium
HelmChartConfig), then the pinned installer was run as root:

```bash
# Place bootstrap configs (Phase 14 / 23.1 / 15 prerequisites)
sudo mkdir -p /etc/rancher/rke2/kubelet.conf.d /var/lib/rancher/rke2/server/manifests
sudo cp /tmp/rke2-stage/config.yaml /etc/rancher/rke2/config.yaml
sudo cp /tmp/rke2-stage/kubelet.conf.d/00-platform.conf /etc/rancher/rke2/kubelet.conf.d/00-platform.conf
sudo cp /tmp/rke2-stage/rke2-cilium-config.yaml /var/lib/rancher/rke2/server/manifests/rke2-cilium-config.yaml

# Install the pinned release (must run as root)
curl -sfL https://get.rke2.io | sudo INSTALL_RKE2_VERSION='v1.36.3+rke2r1' sh -

# Enable + start
sudo systemctl enable rke2-server
sudo systemctl start rke2-server
```

Observed:

- Installer downloaded `v1.36.3+rke2r1`, verified checksums, unpacked to
  `/usr/local`.
- `rke2-server` became `active` and `enabled`.
- Node `alpha` reached `Ready` (control-plane,etcd, v1.36.3+rke2r1,
  containerd 2.3.3-k3s1) after a short bootstrap.
- Core addons all healthy: CoreDNS, metrics-server, Traefik daemonset, Hubble
  relay, Cilium agent daemonset, snapshot-controller.
- The 8 `helm-install-*` jobs reached `Completed`.

**Two bootstrap observations worth recording:**

1. **Traefik install CRD race (resolved automatically).** The first
   `helm-install-rke2-traefik` job briefly errored with
   `Required CRDs are missing...install the corresponding CRD chart first`.
   This is the standard RKE2 CRD bootstrap race; RKE2 retried and Traefik then
   came up `1/1`. No action was needed.

2. **Cilium operator scale-down (single-node optimization).** The bundled
   Cilium chart defaults the operator to **2 replicas** (HA). On a
   single-node cluster the second replica requests host ports that can bind
   only once per node, so it sat `Pending` forever. We set
   `operator.replicas: 1` in the Cilium HelmChartConfig
   (`rke2_cilium_operator_replicas: 1` in defaults). RKE2 reconciled the
   HelmChartConfig and scaled the operator down to 1; the node then had **all
   pods healthy** (13 Running, 8 Completed, zero Pending/error). When more
   nodes join, bump this back to 2.

## 16.2 What was implemented

- `rke2_server` defaults: `rke2_install_script: /tmp/rke2-install.sh`.
- `tasks/main.yml`: install (idempotent via `stat` guard), enable, and start
  `rke2-server`.
- This phase encodes the exact pinned version (Phase 13) and relies on the
  config written in Phases 14, 23.1, and 15 (config.yaml, kubelet drop-in,
  Cilium HelmChartConfig) to be consumed by the very first boot.

## 16.3 Commands run

Validated that `tasks/main.yml` and `defaults/main.yml` both parse as YAML
(Ansible not installed on `alpha`):

```bash
cd /home/jyao/ubuntu-server-iac
python3 - <<'PY'
import yaml
for f in [
  "infra/ansible/roles/rke2_server/tasks/main.yml",
  "infra/ansible/roles/rke2_server/defaults/main.yml",
]:
    with open(f) as fh:
        yaml.safe_load(fh)
    print(f, "OK")
PY
```

Both files parse cleanly. The installer command matches the pinned release
from Phase 13.

</details>

  - ✅ `done` — [inspect Cilium](../reference-design/04-install-rke2-correctly/install-and-start-rke2/inspect-cilium/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — inspect Cilium</summary>

# Phase 25.1 — inspect Cilium

**Intent:** verify the bundled Cilium CNI is running as expected, that
kube-proxy is genuinely disabled (using Cilium's replacement), and that Pod
DNS / service networking works inside the cluster.

## 25.1.1 Cilium pods

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get pods -o wide | grep -i cilium
```

Observed:

```text
cilium-ks259                             1/1   Running    12m   192.168.8.132  alpha
cilium-operator-8569876bb4-mj27t         1/1   Running    12m   192.168.8.132  alpha
helm-install-rke2-cilium-dc76p           0/1   Completed  3m37s 192.168.8.132  alpha
```

Cilium agent daemonset is `Running`; the operator is `Running` (single
replica, per Phase 15 operator scaling); the helm install job `Completed`.

## 25.1.2 Daemonsets

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get daemonset
```

Observed: `cilium` (1/1 Ready) and `rke2-traefik` (1/1 Ready).

## 25.1.3 No kube-proxy DaemonSet

Because we set `disable-kube-proxy: true` (Phase 14) and
`kubeProxyReplacement: true` (Phase 15), kube-proxy must **not** exist:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get ds kube-proxy
```

Expected `NotFound`; observed:

```text
Error from server (NotFound): daemonsets.apps "kube-proxy" not found
```

✅ Confirms Cilium's eBPF kube-proxy replacement is in use.

## 25.1.4 Service networking / DNS inside a Pod

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  run dns-test --rm -it --restart=Never --image=busybox:1.36 \
  -- nslookup kubernetes.default.svc.cluster.local
```

Observed:

```text
Server:    10.43.0.10
Address:   10.43.0.10:53

Name:   kubernetes.default.svc.cluster.local
Address: 10.43.0.1
```

✅ Cluster DNS (`10.43.0.10`) resolves the Kubernetes service (`10.43.0.1`),
proving service networking + DNS work inside a Pod.

## 25.1.5 Result

All checks pass. Combined with Phase 16, **Checkpoint 10 (base cluster gate)**
is satisfied: `alpha Ready`, CoreDNS/Cilium/Traefik/metrics-server running,
DNS + service networking work, no unexplained restarts. A state snapshot was
captured to `~/platform-audit/k8s-first-healthy.txt`.

</details>

  - ✅ `done` — [verify RKE2 Secrets encryption](../reference-design/04-install-rke2-correctly/install-and-start-rke2/verify-rke2-secrets-encryption/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — verify RKE2 Secrets encryption</summary>

# Phase 25.2 — verify RKE2 Secrets encryption

**Intent:** confirm Secrets-at-rest encryption is enabled for the running
cluster via RKE2's `secrets-encrypt` administration command.

## 25.2.1 Status check

```bash
sudo rke2 secrets-encrypt status
```

Observed:

```text
Encryption Status: Enabled
Current Rotation Stage: start
Server Encryption Hashes: All hashes match

Active  Key Type  Name
------  --------  ----
 *      AES-CBC   aescbckey
```

✅ `Encryption Status: Enabled` — Secrets are encrypted at rest with a single
`AES-CBC` key (`aescbckey`), and all server encryption hashes match.

## 25.2.2 Key rotation

Per the reference design, we do **not** rotate keys during initial bootstrap.
Key rotation is a separate maintenance procedure and must be preceded by an
etcd snapshot (see the etcd snapshot schedule configured in Phase 14).

## 25.2.3 Result

Secrets-at-rest encryption is confirmed **Enabled**. No rotation performed.

</details>

- ✅ `done` — [Phase 18 — admin kubeconfig and CLI convenience](../reference-design/04-install-rke2-correctly/admin-kubeconfig-and-cli-convenience/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — admin kubeconfig and CLI convenience</summary>

# Phase 17 — admin kubeconfig and CLI convenience

**Intent:** give the **platform admin only** (`jyao`) the RKE2 admin kubeconfig
and expose `kubectl` / `crictl` for day-to-day admin convenience. Developers do
**not** get this file — they receive their own identities/kubeconfigs later
(Phase 26 RBAC).

## 17.1 Admin kubeconfig

Copied the root-only RKE2 admin kubeconfig into the admin user's home:

```bash
mkdir -p /home/jyao/.kube
sudo cp /etc/rancher/rke2/rke2.yaml /home/jyao/.kube/config
sudo chown -R jyao:jyao /home/jyao/.kube
chmod 600 /home/jyao/.kube/config
```

## 17.2 Point the kubeconfig at the management address

RKE2 generates the admin kubeconfig with `server: https://127.0.0.1:6443`.
The reference design says to change it to the management address so it works
remotely.

> **Design decision — MagicDNS name, not the raw IP.** The reference uses
> `<ALPHA_TAILSCALE_IP>`, but consistent with Phase 14 we used the stable
> Tailscale MagicDNS hostname (`alpha.taild82ced.ts.net`) instead. This name is
> already in the serving certificate's `tls-san`, and unlike the 100.x IP it
> cannot be reallocated. So `kubectl` presents a valid cert and keeps working
> across Tailscale address changes.

```bash
sed -i 's|https://127.0.0.1:6443|https://alpha.taild82ced.ts.net:6443|' /home/jyao/.kube/config
```

Result: `server: https://alpha.taild82ced.ts.net:6443`.

## 17.3 Expose bundled CLI tools

```bash
sudo ln -sf /var/lib/rancher/rke2/bin/kubectl /usr/local/bin/kubectl
sudo ln -sf /var/lib/rancher/rke2/bin/crictl /usr/local/bin/crictl
```

`crictl` also needed to know RKE2's non-standard containerd socket. Created
`/etc/crictl.yaml`:

```yaml
runtime-endpoint: unix:///run/k3s/containerd/containerd.sock
image-endpoint: unix:///run/k3s/containerd/containerd.sock
timeout: 10
debug: false
```

## 17.4 Verify

```bash
export KUBECONFIG=/home/jyao/.kube/config
kubectl get nodes
```

Observed:

```text
NAME    STATUS   ROLES                AGE   VERSION          CONTAINER-RUNTIME
alpha   Ready    control-plane,etcd   16m   v1.36.3+rke2r1   containerd://2.3.3-k3s1
```

`kubectl get nodes` succeeds over the MagicDNS address with a valid cert.
`sudo crictl version` reports containerd `v2.3.3-k3s1`.

## 17.5 What was implemented (Ansible)

- `rke2_server` defaults: `rke2_admin_user`, `rke2_admin_kubeconfig_server`
  (MagicDNS), `rke2_admin_kubeconfig_source`, `rke2_admin_kubeconfig_dest`.
- `tasks/main.yml`: create `kubectl` / `crictl` symlinks, write
  `/etc/crictl.yaml`, copy + own the admin kubeconfig, and rewrite its `server`
  to the management hostname.

## 17.6 Result

Admin access over Tailscale with a valid serving certificate is confirmed.
Developers keep their own identities per Phase 26.

## Addendum — k9s (terminal cluster UI, system-wide)

k9s is a companion terminal UI to `kubectl`. It is **not** in the Ubuntu apt
archive, so the `rke2_server` role installs the official pinned `.deb`
(checksum-verified) into `/usr/bin/k9s` — available to **every** user, who
then runs it against their own OIDC kubeconfig (Phase 27).

Version pinned to `v0.51.0` (release `2026-06-06`, Linux amd64). Pinned in
`infra/ansible/roles/rke2_server/defaults/main.yml`:

```yaml
rke2_k9s_version: "v0.51.0"
rke2_k9s_deb_url: "https://github.com/derailed/k9s/releases/download/v0.51.0/k9s_Linux_amd64.deb"
rke2_k9s_deb_checksum: "56b539a509eb2d6357cf4f575ed38c089f0e4880c95f79a70196b54f14954908"
rke2_k9s_deb_dest: /tmp/k9s_linux_amd64.deb
```

`tasks/main.yml` downloads the `.deb` with `get_url` (asserting the sha256
checksum), installs it with `apt: deb:`, then removes the staged file.

Verified the pinned artifact before wiring it in: downloaded the exact `.deb`
and confirmed `sha256sum -c` passes and `k9s version` reports `v0.51.0`
(commit `558caafe7b`).

Deployment is handled by the playbook (run as root), or targeted with the
`k9s` tag:

```bash
cd /home/jyao/ubuntu-server-iac/infra
sudo ansible-playbook -i inventory/production.yml ansible/site.yml \
  --limit alpha --connection local --tags k9s
# PLAY RECAP alpha: ok=6 changed=3 failed=0
```

Installed on alpha:

```bash
which k9s          # /usr/bin/k9s
k9s version        # v0.51.0 (commit 558caafe7b, 2026-06-06)
```

After install, any user can launch against their context, e.g.
`k9s --context alpha-dev` (or just `k9s` for the default context).

## 17.7 Live ingress validation — `demo-meme` tenant app

Used the working admin kubeconfig to deploy a throwaway tenant app that
exercises the Traefik ingress path end to end (Deployment → Service →
Ingress → node port 80). This is a hand-applied smoke test, **not** yet
GitOps-managed; it will be adopted into the GitOps source of truth during the
Part V bootstrap.

Manifests live under `infra/kubernetes/tenants/demo-meme/`:

```bash
cd /home/jyao/ubuntu-server-iac/infra/kubernetes/tenants/demo-meme
export KUBECONFIG=/home/jyao/.kube/config
kubectl apply -f namespace.yaml -f configmap.yaml -f deployment.yaml -f service.yaml -f ingress.yaml
kubectl -n demo-meme rollout status deploy/meme-site --timeout=120s
```

Verified:

- `pod/meme-site-*` reached `1/1 Running`.
- `service/meme-site` ClusterIP `10.43.247.243:80` targeting the pod.
- Ingress `meme-site` (class `traefik`) routes `meme.alpha.taild82ced.ts.net`
  to the service.
- `curl -H 'Host: meme.alpha.taild82ced.ts.net' http://127.0.0.1` returns
  `HTTP/1.1 200 OK` with the meme homepage HTML.
- The page loads `https://http.cat/200` (reachable, HTTP 200).

This confirms the bundled Traefik ingress controller is serving traffic and the
node port 80 path works before Phase 18's reboot-recovery check.

</details>

- ✅ `done` — [Phase 19 — verify reboot recovery now, not later](../reference-design/04-install-rke2-correctly/verify-reboot-recovery-now-not-later/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — verify reboot recovery now, not later</summary>

# Phase 18 — verify reboot recovery now, not later

**Intent:** prove that a normal reboot brings the whole platform back with
**zero manual intervention** — no manual `docker start`, no manual `kubectl
apply`, no manual CNI repair (Checkpoint 11). Because the cluster state lives
in etcd on disk, workloads (like the `demo-meme` Deployment) are recreated by
the controllers automatically.

## 18.1 Pre-reboot baseline

Captured immediately before rebooting:

```bash
export KUBECONFIG=/home/jyao/.kube/config
systemctl is-active rke2-server      # active
kubectl get nodes                     # alpha Ready control-plane,etcd
kubectl get pods -A                   # all Running / Completed
kubectl -n demo-meme get pods         # meme-site-* 1/1 Running
uptime -p                             # up 23 hours, 49 minutes
```

Baseline was clean: control plane pods (`kube-apiserver`, `etcd`,
`kube-scheduler`, `kube-controller-manager`), Cilium + operator, CoreDNS,
Traefik, metrics-server, snapshot-controller, and the `demo-meme` app were all
healthy.

## 18.2 Reboot

```bash
sudo reboot
```

SSH re-established once the host was back.

## 18.3 Post-reboot recovery check

```bash
systemctl is-active rke2-server
kubectl get nodes
kubectl get pods -A
kubectl -n demo-meme get pods
```

Wait for reconciliation, then record boot time:

```bash
systemd-analyze
systemd-analyze blame | head -30
```

## 18.4 Checkpoint 1

Recovery requires:

```text
zero manual "docker start"
zero manual "kubectl apply"
zero manual CNI repair
```

The `demo-meme` pod must be recreated by the Deployment controller, and the
node must return to `Ready`.

## 18.5 Post-reboot observations (live)

Verified after the host came back:

```bash
uptime -p                 # up 19 minutes  -> reboot confirmed
systemctl is-enabled rke2-server   # enabled
systemctl is-active rke2-server    # active
systemctl --failed --no-legend | wc -l   # 0
kubectl get nodes         # alpha Ready
kubectl get pods -A       # 14 Running, 8 Completed
```

- Node `alpha` `Ready`, `containerd://2.3.3-k3s1`, Ubuntu 26.04.
- `rke2-server` **enabled** and **active**; **0 failed systemd units**.

## 18.6 `demo-meme` survivor probe

```bash
kubectl -n demo-meme get pods
```

```text
NAME-                         READY   STATUS    RESTARTS      AGE
meme-site-7486bc7c98-cqkg4   1/1     Running   1 (19m ago)   26m
```

`RESTARTS 1 (19m ago)` matches the reboot window — the kubelet recreated the
pod by itself. Deployment UID unchanged (`d6104ebf-…`), so it is the same
Deployment (no manual re-apply). Still serving after reboot:

```bash
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://10.43.247.243/
curl -s -o /dev/null -w 'HTTP %{http_code} %{content_type}\n' http://10.43.247.243/meme.svg
```

```text
HTTP 200
HTTP 200 image/svg+xml
```

## 18.7 Boot timing

```bash
systemd-analyze time
```

```text
Startup finished in 2min 8.556s (firmware) + 1.515s (loader) + 2.650s (kernel) +
 7.480s (initrd) + 9.590s (userspace) = 2min 29.793s
graphical.target reached after 9.328s in userspace.
```

Boot ID after reboot: `064aa60d-d349-4258-add6-3a6da3c426c4`.

## 18.8 Result — Checkpoint 11 passed

The reboot required **zero** manual container starts, **zero** manual
`kubectl apply`, and **zero** manual CNI repair. Node, add-ons, and the
`demo-meme` tenant all recovered automatically. This closes the reboot-risk
gate before adding more components.

## 18.9 Follow-up incident — DHCP IP drift took the cluster down

**Symptom:** `rke2-server` stuck in `activating`, `kubectl` unresponsive.
`journalctl -u rke2-server` showed the etcd peer mismatch:

```text
Found [alpha-49ad8379=https://192.168.8.132:2380], expect:
  ... https://192.168.8.137:2380
```

**Root cause:** `enp193s0` was on **DHCP** and the lease moved across reboots
(`192.168.8.132` → `192.168.8.137`). RKE2 derives its etcd peer/advertise URLs
from the node IP, so an IP change left etcd's membership pointing at an
address the node no longer held.

**Fix (do this on any RKE2 server running on DHCP):**

1. Pin the LAN interface to a **static, uncommon** address so it can't collide
   with the DHCP pool — `192.168.8.240` (high range, avoids `.132–.150` DHCP
   range) — in `/etc/netplan/00-installer-config.yaml` (`dhcp4: false`), then
   `sudo netplan apply`.
2. Pin RKE2's `node-ip` to the same address so RKE2 is decoupled from the
   interface lease entirely. Append to `/etc/rancher/rke2/config.yaml`:

```yaml
# Pinned node-ip to the static LAN address (192.168.8.240) so the etcd
# peer/advertise URLs no longer depend on the DHCP lease. See netplan.
node-ip: 192.168.8.240
```

3. Reconcile the already-booted etcd. For a **single-node** control plane the
   recovery is a cluster-reset (forgets stale peers, becomes sole member again
   using the current node-ip, keeps existing data dir):

```bash
sudo systemctl stop rke2-server
sudo rke2 server --cluster-reset            # resets membership, backs up certs
sudo systemctl start rke2-server
```

4. Verify etcd now advertises the new address and the node is healthy:

```bash
sudo cat /var/lib/rancher/rke2/server/db/etcd/config | grep -E 'advertise|initial-cluster'
# expect: https://192.168.8.240:2380  (NOT the old lease)
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
kubectl get nodes -o wide          # alpha Ready, INTERNAL-IP 192.168.8.240
kubectl get pods -A | grep -vE 'Running|Completed'
```

**Verified (live):** etcd config regenerated with `initial-cluster:
alpha-107afd20=https://192.168.8.240:2380` and
`advertise-client-urls: https://192.168.8.240:2379`; `alpha` returned to
`Ready` at `192.168.8.240`; Cilium, Traefik, CoreDNS, and Kyverno all recovered;
the `42wasd` app returned to `1/1 Running` and served `HTTP 200` through the
ingress. The DHCP IP drift is now impossible because the address is static in
both netplan and `node-ip`.

</details>


### 100% — Part V — GitOps bootstrap

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:100.0%"></div></div><div class="progress-pct" style="font-size:.85em;">100%</div><div class="tip-box"><strong>Done (12)</strong>
• install Argo CD exactly once by hand
• root GitOps application
• AppProjects
• namespace baseline
• PriorityClasses
• ResourceQuota
• LimitRange
• default-deny NetworkPolicy
• RBAC
• dev Role
• production is intentionally different
• authentication for Kubernetes developers
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

- ✅ `done` — [Phase 20 — install Argo CD exactly once by hand](../reference-design/05-gitops-bootstrap/install-argo-cd-exactly-once-by-hand/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — install Argo CD exactly once by hand</summary>

# Phase 19 — install Argo CD exactly once by hand

**Intent:** do the one manual, minimal install of Argo CD that bootstraps
itself out of the paradox ("Argo cannot install itself before Argo exists").
Everything managed inside Kubernetes after this point goes through Git + Argo.

## 19.1 Pin the version

Latest release at install time was `v3.5.1` (verified against the GitHub
releases API). Kubernetes is `v1.36.3`, compatible.

```bash
export ARGOCD_VERSION="v3.5.1"
```

## 19.2 Install (server-side apply)

```bash
export KUBECONFIG=/home/jyao/.kube/config
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd --server-side --force-conflicts \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
```

Applied CRDs, ServiceAccounts, RBAC, ConfigMaps, Secrets, Services,
Deployments, a StatefulSet (`argocd-application-controller`), and NetworkPolicies.

## 19.3 Wait and verify

```bash
kubectl -n argocd rollout status deployment/argocd-server --timeout=180s
kubectl -n argocd get pods
```

All 7 pods `Running`:

```text
argocd-application-controller-0            1/1 Running
argocd-applicationset-controller-...       1/1 Running
argocd-dex-server-...                      1/1 Running
argocd-notifications-controller-...        1/1 Running
argocd-redis-...                           1/1 Running
argocd-repo-server-...                     1/1 Running
argocd-server-...                          1/1 Running
```

## 19.4 Initial admin access

Not exposed publicly (per design). Credentials:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

The `argocd-server` Service is `ClusterIP`, `80/TCP,443/TCP`. Verified reachable:

```bash
kubectl -n argocd port-forward svc/argocd-server 8443:443 &
curl -sk -o /dev/null -w 'HTTPS %{http_code}\n' https://127.0.0.1:8443/   # 200
```

## 19.5 Result

Argo CD v3.5.1 is running as the platform's GitOps owner. It is **not**
publicly exposed; temporary access is via `kubectl port-forward`. Next: Phase 20
root GitOps application (App-of-Apps bootstrap).

</details>

- ✅ `done` — [Phase 21 — root GitOps application](../reference-design/05-gitops-bootstrap/root-gitops-application/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — root GitOps application</summary>

# Phase 20 — root GitOps application

**Intent:** stand up the **App-of-Apps** bootstrap so Argo CD owns Kubernetes
configuration from here on. One root Application (`platform-root`) watches a
directory of child `Application` objects.

## 20.1 Manifests

Created under `infra/kubernetes/bootstrap/argocd/`:

- `platform-root.yaml` — root App-of-Apps Application pointing at
  `infra/kubernetes/bootstrap/argocd/apps` (recurse).
- `apps/platform-namespaces.yaml` — child Application for the namespace
  baseline, `sync-wave -20` so namespaces exist first.
- `projects.yaml` — AppProjects: `platform`, `tenant-jya0`,
  `tenant-42wasd-admin`.

The repo is public, so Argo CD clones it over HTTPS with no stored credential.

```bash
kubectl apply -f infra/kubernetes/bootstrap/argocd/projects.yaml
kubectl apply -f infra/kubernetes/bootstrap/argocd/platform-root.yaml
```

## 20.2 Result

```bash
kubectl -n argocd get applications
```

```text
NAME                  SYNC STATUS   HEALTH STATUS
platform-namespaces   Synced        Healthy
platform-root         Synced        Healthy
```

Both synced automatically (automated sync, prune + selfHeal, server-side
apply). The child `platform-namespaces` app was created by the root app with no
manual `kubectl apply`.

## 20.3 From here on

```text
if it belongs inside Kubernetes
    -> prefer Git + Argo
```

not manual `kubectl apply`. This was the last hand-applied piece of platform
config (besides Argo CD itself, Phase 19).

</details>

  - ✅ `done` — [AppProjects](../reference-design/05-gitops-bootstrap/root-gitops-application/appprojects/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — AppProjects</summary>

# AppProjects (29.1)

Created three AppProjects in `infra/kubernetes/bootstrap/argocd/projects.yaml`:

- **`platform`** — cluster-wide resources (namespaces `*`, kinds `*`).
- **`tenant-jya0`** — constrained to `dev-jya0`, `prd-jya0`.
- **`tenant-42wasd-admin`** — constrained to `dev-42wasd-admin`,
  `prd-42wasd-admin`, `mlops`, `dev-games-42wasd-admin`,
  `prd-games-42wasd-admin`.

Both tenant projects allow only the single infra repo as a source, and only
themselves as destinations. This is a second boundary alongside Kubernetes RBAC.

Applied:

```bash
kubectl apply -f infra/kubernetes/bootstrap/argocd/projects.yaml
# appproject.argoproj.io/platform created
# appproject.argoproj.io/tenant-jya0 created
# appproject.argoproj.io/tenant-42wasd-admin created
```

Note: the AppProject `destinations` field uses the singular `namespace` key
(not `namespaces`), which strict decoding rejects.

---

## Follow-on: `tenant-community-web` (public web app in GitOps)

The 42WASD community website (`prd-42wasd-admin`) was previously applied to
the cluster by hand (no `argocd.argoproj.io/` tracking). Wired it into GitOps
so Argo CD owns the Deployment/Service/Ingress/NetworkPolicy/PVC, using the
same tenant-project pattern as the games cluster.

- `projects.yaml` — added `https://github.com/42WASD/42wasd-community-web.git`
  to `tenant-42wasd-admin` `sourceRepos` (its `prd-42wasd-admin` destination
  already existed).
- `apps/tenant-community-web.yaml` — Application, project
  `tenant-42wasd-admin`, source repo `42wasd-community-web.git` path
  `deploy/k8s`, dest `prd-42wasd-admin`, auto-sync + prune + selfHeal,
  `ServerSideApply=true`.

```bash
# AppProject is NOT Argo-managed -> apply manually (see gotcha above).
kubectl -n argocd apply -f infra/kubernetes/bootstrap/argocd/projects.yaml
kubectl -n argocd apply -f infra/kubernetes/bootstrap/argocd/apps/tenant-community-web.yaml
kubectl -n argocd get app tenant-community-web   # Synced
```

The Deployment mounts a writable `42wasd-data` PVC (nvme-fast, 1Gi, RWO) at
`/app/data` with `fsGroup: 1654` so `saveProfile` can persist `players.json`,
seeded by a non-root `seed-data` initContainer, and uses `strategy: Recreate`
(because the RWO volume can't be shared during a rolling update). Details and
verification live in the `42wasd-community-web` repo runbook
(`phase-18-production-hardening`).

> App health may read "Progressing" while the Deployment is actually Healthy:
> the Traefik Ingress does not populate `status.loadBalancer`, which ArgoCD's
> Ingress health hook treats as "not ready yet". Cosmetic only; the site serves
> HTTP 200 by hostname.

</details>

- ✅ `done` — [Phase 22 — namespace baseline](../reference-design/05-gitops-bootstrap/namespace-baseline/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — namespace baseline</summary>

# Phase 21 — namespace baseline

Created the platform and tenant namespace baseline as code, managed by Argo CD
(the `platform-namespaces` child app from Phase 20).

## 21.1 Manifests

`infra/kubernetes/platform/namespaces/`:

- `platform.yaml` — `kyverno`, `openebs`, `monitoring`, `registry`, `security`,
  `ingress`, `build` (label `platform.tier: platform`).
- `tenants.yaml` — `dev-jya0`, `prd-jya0`, `dev-42wasd-admin`,
  `prd-42wasd-admin`, `mlops`, `dev-games-42wasd-admin`,
  `prd-games-42wasd-admin`, each labelled with `platform.tier: tenant` and Pod
  Security `restricted` (enforce/audit/warn).

`mlops` replaces the earlier per-tenant `ml-jya0`/`gpu-jya0` as a single shared
ML namespace: models are heavy on GPU and are consumed concurrently by any
namespace that wants to use them, so the model/GPU pool is shared rather than
duplicated per tenant (see reference namespace reference). The games lane is split into `dev-games-42wasd-admin` (ephemeral
staging) and `prd-games-42wasd-admin` (canonical) per the deep-copy-on-demand
methodology in Phase 53.

Infrastructure namespaces (`kube-system`, CNI, `argocd`) are **not** labelled
`restricted` — their trusted controllers need a less restrictive policy, per the
reference note.

## 21.2 Verified

```bash
kubectl get ns -l platform.tier=platform   # 7 platform namespaces Active
kubectl get ns -l platform.tier=tenant     # 7 tenant namespaces
kubectl get ns dev-games-42wasd-admin -o jsonpath='{.metadata.labels}'
# pod-security.kubernetes.io/{enforce,audit,warn}=restricted
```

The tenant namespaces carry the `restricted` Pod Security labels; platform
namespaces do not. The old `prod-jya0`/`ml-jya0`/`gpu-jya0`/`dev-42admin`/
`prod-42admin`/`games-42admin` namespaces are removed by Argo CD's prune since
they are no longer in the manifest.

</details>

- ✅ `done` — [Phase 23 — PriorityClasses](../reference-design/05-gitops-bootstrap/priorityclasses/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — PriorityClasses</summary>

# Phase 22 — PriorityClasses
# Phase 22 — PriorityClasses

Created a small, deliberately non-inflated set of `PriorityClass` resources so
the scheduler can preempt low-value disposable workloads before starving
critical platform or production ones.

## 22.1 Manifests

`infra/kubernetes/platform/priorityclasses/priorityclasses.yaml`:

| PriorityClass               | value   | purpose |
| --------------------------- | ------- | ------- |
| `platform-critical-custom`  | 100000  | Critical platform workloads (platform admins). |
| `prod-high`                 | 20000   | Tenant production workloads. |
| `dev-normal`                | 1000    | Normal development workloads. |
| `build-low`                 | -1000   | Build / disposable workloads that yield first. |

No `globalDefault` is set, so ordinary pods get the default priority and
elevated classes must be requested explicitly.

Avoiding giant inflation: if every tenant could declare
`platform-critical`, priority is meaningless. Restricting who may use the
elevated classes is delegated to RBAC/Kyverno in a later phase.

Managed by a new Argo child app `platform-priorityclasses` (sync-wave `-20`,
so they exist before namespaces/quota apps). The `platform-root` app
auto-discovers it from `infra/kubernetes/bootstrap/argocd/apps`.

## 22.2 Applied via Argo CD

```bash
kubectl -n argocd get applications
# platform-priorityclasses  Synced  Healthy
```

```bash
kubectl get priorityclasses
# NAME                      VALUE
# platform-critical-custom  100000
# prod-high                 20000
# dev-normal                1000
# build-low                 -1000
```

The elevated `platform-critical-custom` class exists now; who may use it is
enforced later (RBAC / admission), not by the class itself.

</details>

- ✅ `done` — [Phase 24 — ResourceQuota](../reference-design/05-gitops-bootstrap/resourcequota/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — ResourceQuota</summary>

# Phase 23 — ResourceQuota

Applied a `namespace-budget` ResourceQuota to every tenant namespace as a
**ceiling** (not a reservation). Ceilings may sum beyond physical capacity; the
sum of actually-scheduled requests cannot.

## 23.1 Manifests

`infra/kubernetes/platform/quotas/`:

- `jya0.yaml` — `dev-jya0`, `prd-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin`, `prd-42wasd-admin`
- `mlops.yaml` — `mlops`, includes `requests.nvidia.com/gpu: "1"` ceiling
- `games.yaml` — `prd-games-42wasd-admin` (canonical) and
  `dev-games-42wasd-admin` (ephemeral staging, intentionally small)

Values come from the initial quota reference (`02-110`), with game lanes
documented as "tune after games".

Managed by a new Argo child app `platform-quotas` (sync-wave `-10`) in
`infra/kubernetes/bootstrap/argocd/apps/platform-quotas.yaml`. The
`platform-root` app auto-discovered it after a hard refresh.

## 23.2 Applied via Argo CD

```bash
kubectl -n argocd get applications
# platform-quotas  Synced  Healthy
```

Verified a `namespace-budget` quota in every tenant namespace:

```bash
for ns in dev-jya0 prd-jya0 dev-42wasd-admin prd-42wasd-admin mlops \
          dev-games-42wasd-admin prd-games-42wasd-admin; do
  kubectl -n $ns get resourcequota namespace-budget --no-headers
done
```

`mlops` hard limits include:

```json
{"requests.nvidia.com/gpu":"1","requests.cpu":"8","limits.cpu":"16",
 "requests.memory":"16Gi","limits.memory":"32Gi", ...}
```

The GPU ceiling is defined now; the physical GPU is added in a later phase.
GPU is governed by quota + admission, not namespace splitting.

</details>

- ✅ `done` — [Phase 25 — LimitRange](../reference-design/05-gitops-bootstrap/limitrange/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — LimitRange</summary>

# Phase 24 — LimitRange

Added a `container-defaults` LimitRange to every tenant namespace so that a
container with `resources: {}` is not silently unbounded. The LimitRange
supplies sensible `defaultRequest` / `default` / `max` per container that fit
inside each namespace's `namespace-budget` ResourceQuota ceiling.

## 24.1 Manifests

`infra/kubernetes/platform/limitranges/`:

- `jya0.yaml` — `dev-jya0`, `prd-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin`, `prd-42wasd-admin`
- `mlops.yaml` — `mlops` (higher defaults; GPU-backed serving)
- `games.yaml` — `prd-games-42wasd-admin` (canonical) and
  `dev-games-42wasd-admin` (ephemeral staging, intentionally small)

Per-container shape (varies by namespace):

```yaml
defaultRequest: cpu 250m / memory 256Mi / eph 512Mi
default:        cpu 1    / memory 1Gi  / eph 2Gi
max:            cpu 4    / memory 8Gi  / eph 20Gi
```

`prd-jya0` example (verified on cluster):

```json
defaultRequest: {"cpu":"500m","memory":"512Mi","ephemeral-storage":"1Gi"}
default:        {"cpu":"2","memory":"2Gi","ephemeral-storage":"4Gi"}
max:            {"cpu":"8","memory":"16Gi","ephemeral-storage":"30Gi"}
```

Managed by a new Argo child app `platform-limitranges` (sync-wave `-10`) in
`infra/kubernetes/bootstrap/argocd/apps/platform-limitranges.yaml`. The
`platform-root` app auto-discovered it after a hard refresh.

## 24.2 Applied via Argo CD

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-limitranges  Synced  Healthy
```

Verified a `container-defaults` LimitRange in every tenant namespace:

```bash
for ns in dev-jya0 prd-jya0 dev-42wasd-admin prd-42wasd-admin mlops \
          dev-games-42wasd-admin prd-games-42wasd-admin; do
  kubectl -n $ns get limitrange container-defaults --no-headers
done
```

Together with Phase 23's quota, a container that omits resource limits is
now given a bounded default instead of unbounded consumption.

</details>

- ✅ `done` — [Phase 26 — default-deny NetworkPolicy](../reference-design/05-gitops-bootstrap/default-deny-networkpolicy/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — default-deny NetworkPolicy</summary>

# Phase 25 — default-deny NetworkPolicy

Added a `default-deny` NetworkPolicy (Ingress + Egress) to every tenant
namespace, plus an `allow-cluster-dns` egress rule so workloads can still
resolve CoreDNS. Additional per-application flows are added later as needed.

## 25.1 Manifests

`infra/kubernetes/platform/networkpolicies/`:

- `jya0.yaml` — `dev-jya0`, `prd-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin`, `prd-42wasd-admin`, `mlops`
- `games.yaml` — `prd-games-42wasd-admin` (canonical) and
  `dev-games-42wasd-admin` (ephemeral staging)

Each namespace gets:

```yaml
# default-deny
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]

# allow-cluster-dns
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports: [UDP 53, TCP 53]
```

Enforced by the bundled Cilium CNI (network policy mode on).

Managed by a new Argo child app `platform-networkpolicies` (sync-wave `-5`)
in `infra/kubernetes/bootstrap/argocd/apps/platform-networkpolicies.yaml`.
The `platform-root` app auto-discovered it after a hard refresh.

## 25.2 Applied via Argo CD

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-networkpolicies  Synced  Healthy
```

Verified `default-deny` + `allow-cluster-dns` in every tenant namespace:

```bash
for ns in dev-jya0 prd-jya0 dev-42wasd-admin prd-42wasd-admin mlops \
          dev-games-42wasd-admin prd-games-42wasd-admin; do
  kubectl -n $ns get networkpolicies
done
```

The existing `demo-meme` workload lives in a separate non-tenant namespace
and is unaffected (still Running).

## 25.3 Every tenant must also reach the kube-apiserver

Because the apiserver is **self-hosted** (static pod on the node), the
`kubernetes` Service backend is the **node IP**, not a pod IP. Cilium CIDR
selectors ignore node addressing by default, so an egress `default-deny`
policy **cannot** allow the apiserver with an `ipBlock: 0.0.0.0/0` rule. The
correct mechanism is Cilium's `kube-apiserver` **entity**, applied once
cluster-wide in
`infra/kubernetes/platform/networkpolicies/00-allow-kube-apiserver.yaml`,
managed by the `platform-networkpolicies` Argo app.

```bash
kubectl get ciliumclusterwidenetworkpolicies.cilium.io allow-to-kube-apiserver
```

## 25.4 INCIDENT (2026-08-24): blanket `endpointSelector: {}` broke cluster egress

The CCNP was first applied with `endpointSelector: {}` (commit `c9795ad`).
In Cilium, **any** endpoint selected by a policy becomes default-deny for
traffic the policy does not explicitly allow. A blank `{}` selector therefore
made **every** pod in the cluster egress default-deny — including `kube-system`
and `ingress` namespaces that were never meant to be default-deny.

**Impact:** Cloudflare tunnel `CrashLoopBackOff` (SRV lookup `argotunnel.com`
timeout), CoreDNS `SERVFAIL` (blocked upstream to `8.8.8.8`), and app jar
downloads blocked (velocity / paper `ImagePullBackOff`).

**Detection** (Cilium monitor drops):

```text
identity 27913->world: 10.42.0.130:42608 -> 8.8.8.8:53 udp   (CoreDNS)
identity 1948->world: 10.42.0.106:41262 -> 1.1.1.1:853 tcp    (cloudflared)
```

**Fix (applied live + repo):** scoped the selector to only the tenant
namespaces that carry `default-deny` and genuinely need the apiserver:

```yaml
spec:
  endpointSelector:
    matchExpressions:
      - key: k8s:io.cilium.k8s.namespace.labels.kubernetes.io/metadata.name
        operator: In
        values:
          - prd-42wasd-admin
          - prd-games-42wasd-admin
          - prd-jya0
          - dev-42wasd-admin
          - dev-games-42wasd-admin
          - dev-jya0
          - mlops
  egress:
    - toEntities:
      - kube-apiserver
```

**Verify (restored egress):**

```bash
kubectl run -it --rm egress-check --image=curlimages/curl -- \
  curl -s -o /dev/null -w '%{http_code}\n' https://1.1.1.1
# -> 301
```

cloudflared back to `2/2 Running` with HTTP/2 connections to the Cloudflare
edge; tunnel endpoint returned `200`; DNS resolvable. (Cloudflare QUIC fails
but HTTP/2 TCP fallback works — acceptable.)

**Lesson:** never use `endpointSelector: {}` for an egress-only CCNP. Scope
to the specific tenant namespaces and keep the list in sync with the
per-namespace default-deny NetworkPolicies.

</details>

- ✅ `done` — [Phase 27 — RBAC](../reference-design/05-gitops-bootstrap/rbac/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — RBAC</summary>

# Phase 26 — RBAC

Added namespace-scoped Roles and RoleBindings so tenant groups can work in
their own namespaces, with dev namespaces allowing writes and prod (and
`mlops`) read-only — application writes in prod come from Argo CD, not from
developer credentials.

## 26.1 Manifests

`infra/kubernetes/platform/rbac/`:

- `jya0.yaml` — `dev-jya0` (writer), `prd-jya0` (reader) for group `tenant-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin` (writer),
  `prd-42wasd-admin` (reader), `mlops` (reader) for group `tenant-42wasd-admin`
- `games.yaml` — `dev-games-42wasd-admin` (writer),
  `prd-games-42wasd-admin` (reader) for group `tenant-42wasd-admin`

Roles:

- `tenant-developer` — full CRUD on pods/services/endpoints/configmaps/PVCs,
  deployments/replicasets/statefulsets, jobs/cronjobs, plus exec/portforward.
- `tenant-reader` — `get`/`list`/`watch` on the same resource set.

Prod is read-only on purpose: a principal that can create arbitrary prod
Pods can mount Secrets from that namespace even if RBAC denies direct
`get secret`, so writes are confined to Argo CD.

Managed by a new Argo child app `platform-rbac` (sync-wave `-5`) in
`infra/kubernetes/bootstrap/argocd/apps/platform-rbac.yaml`.

## 26.2 Applied via Argo CD

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-rbac  Synced  Healthy
```

Verified every tenant namespace has the expected Role + RoleBinding.

## 26.3 Verified with `kubectl auth can-i`

```bash
kubectl auth can-i create deployments -n dev-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # yes
kubectl auth can-i create deployments -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
kubectl auth can-i get pods -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # yes
kubectl auth can-i get secrets -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
```

Dev group gets writes; prod/`mlops` get read-only and no secret access.
Authentication (Phase 27) is handled separately via OIDC later; this phase is
authorization only.

</details>

  - ✅ `done` — [dev Role](../reference-design/05-gitops-bootstrap/rbac/dev-role/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — dev Role</summary>

# dev Role (26.1)

The `tenant-developer` Role grants full CRUD on pods, services, endpoints,
configmaps, PVCs, deployments/replicasets/statefulsets, jobs/cronjobs, plus
`exec`/`portforward`, scoped to a single dev namespace. The RoleBinding binds
the identity group (e.g. `tenant-42wasd-admin`) into that namespace.

Part of Phase 26 — RBAC, applied via Argo CD:

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-rbac  Synced  Healthy
```

Verified the `dev-42wasd-admin` namespace has the expected Role + RoleBinding.

</details>

  - ✅ `done` — [production is intentionally different](../reference-design/05-gitops-bootstrap/rbac/production-is-intentionally-different/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — production is intentionally different</summary>

# production is intentionally different (26.2)

In prod namespaces developers are read-only (`get`/`list`/`watch`/`logs`/
`events`, possibly port-forward). Application writes come exclusively from
Argo CD. A principal that can create arbitrary prod Pods can mount Secrets
from that namespace even if RBAC denies direct `get secret`, so giving devs
write access in prod would make the "cannot read Secret" boundary meaningless.

Verified with `kubectl auth can-i` (as the tenant group):

```bash
kubectl auth can-i create deployments -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
kubectl auth can-i get pods -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # yes
kubectl auth can-i get secrets -n prd-42wasd-admin \
  --as=system:serviceaccount --as-group=tenant-42wasd-admin   # no
```

</details>

- ✅ `done` — [Phase 28 — authentication for Kubernetes developers](../reference-design/05-gitops-bootstrap/authentication-for-kubernetes-developers/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — authentication for Kubernetes developers</summary>

# Phase 27 — authentication for Kubernetes developers (Dex + GitHub OIDC)

Implemented Dex as the in-cluster OIDC identity provider, wired to GitHub
OAuth, and configured `kube-apiserver` to authenticate via OIDC. Developers
use `kubectl oidc-login` (device-code flow, RFC 8628) for headless login on
the host.

## 27.1 Decisions

| Decision | Choice | Why |
|---|---|---|
| Issuer hostname | `https://alpha.taild82ced.ts.net` (port 443) | Tailscale issues certs **only for the node's own FQDN** — no subdomains (`tailscale cert dex.alpha…` → "invalid domain"). Traefik (default ingress, `websecure`/443) routes the issuer; kube-apiserver stays on 6443 → no port conflict. |
| Group mapping | Bind RBAC to `42WASD:<team>` | Dex GitHub groups are always `<org>:<team>` and cannot drop the org prefix. Updated Phase 26 RoleBindings to bind `42WASD:tenant-jya0` / `42WASD:tenant-42wasd-admin`. |
| Secrets | Manual `kubectl` provision | GitHub OAuth `client_id`/`secret` and the Dex client secret are never committed (no secrets tooling in repo yet). |
| TLS | Tailscale cert via Traefik | `sudo tailscale cert alpha.taild82ced.ts.net` works; store as a `tls` Secret `tailscale-cert`. |

## 27.2 Manifests

`infra/kubernetes/platform/dex/`:

- `deployment.yaml` — Dex `v2.45.1` Deployment (1 replica, SQLite on a
  `nvme-fast` PVC), `dex` Service (5556), ServiceAccount.
- `configmap.yaml` — Dex config: issuer, GitHub connector (org `42WASD`,
  teams `tenant-jya0` / `tenant-42wasd-admin`, `teamNameField: slug`),
  `staticClients` `kubernetes` with `publicGrantTypes` device-code.
- `ingress.yaml` — `IngressRoute` (Traefik) terminating TLS with the
  `tailscale-cert` Secret.

`infra/kubernetes/bootstrap/argocd/apps/platform-dex.yaml` — new Argo child
app (project `platform`, sync-wave `-3`, auto-discovered by `platform-root`).

`infra/kubernetes/platform/rbac/` — updated all RoleBinding subjects to
`42WASD:tenant-jya0` / `42WASD:tenant-42wasd-admin`.

`infra/ansible/roles/rke2_server/` — added `rke2_oidc_*` vars and
`kube-apiserver-arg` OIDC block (enabled via `rke2_oidc_enabled` in
`alpha.yml`).

## 27.3 Commands run

Validate the manifests server-side (dry-run):

```bash
cd infra/kubernetes/platform/dex
kubectl apply --dry-run=server -f deployment.yaml   # dex, service, pvc, sa
kubectl apply --dry-run=server -f configmap.yaml     # dex-config
kubectl apply --dry-run=server -f ingress.yaml        # ingressroute.traefik.io/dex
```

Provision the TLS Secret from the Tailscale cert (root-owned temp files):

```bash
sudo tailscale cert alpha.taild82ced.ts.net
kubectl -n security create secret tls tailscale-cert \
  --cert=alpha.taild82ced.ts.net.crt --key=alpha.taild82ced.ts.net.key \
  --dry-run=client -o yaml | kubectl apply -f -
rm -f alpha.taild82ced.ts.net.crt alpha.taild82ced.ts.net.key
```

Provision the GitHub OAuth + Dex client Secrets (values supplied interactively
by the developer, never committed):

```bash
kubectl -n security create secret generic dex-github-oauth \
  --from-literal=client-id='<GH_APP_CLIENT_ID>' \
  --from-literal=client-secret='<GH_APP_CLIENT_SECRET>' \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n security create secret generic dex-client \
  --from-literal=client-secret='<RANDOM_LONG_SECRET>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

Sync via Argo CD (refresh root, then sync the child app):

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
kubectl -n argocd patch application platform-dex \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"apply":{"force":true}}}}}'
```

### Debug fixes

1. **Dex CrashLoopBackOff — SQLite write permission.** Fresh hostpath/LVM
   PVC is root-owned but the Dex image runs as UID 1000. Fixed with a pod
   `securityContext` on the Deployment (`runAsUser: 1000, runAsGroup: 1000,
   fsGroup: 1000`). Had to force-delete the old pod to release the RWO PVC
   before the fixed pod could mount.

2. **Issuer 404 with the default Traefik cert.** RKE2's bundled Traefik runs
   with `--providers.kubernetescrd.ingressClass=traefik`, so an IngressRoute
   without `spec.ingressClassName: traefik` is **ignored** (default cert +
   404). Added `ingressClassName: traefik`, dropped the redundant
   `traefik.ingress.kubernetes.io/router.entrypoints` annotation and the
   `PathPrefix('/')` from the Host rule. Verified issuer returns 200 with the
   Let's Encrypt cert for `CN=alpha.tail.iota.ts.net`.

### 27.3.1 Apply the RKE2 OIDC flags (control-plane change)

RKE2 renders its config from `/etc/rancher/rke2/config.yaml`. Add the
`kube-apiserver-arg` block, validate YAML, then restart `rke2-server` (brief
API downtime). A timestamped backup is written before editing.

```bash
sudo cp /etc/rancher/rke2/config.yaml /etc/rancher/rke2/config.yaml.bak-$(date +%Y%m%d-%H%M%S)
# insert the kube-apiserver-arg OIDC block (see 27.2 manifests / role template)
sudo python3 - <<'PY'
from pathlib import Path
p = Path('/etc/rancher/rke2/config.yaml')
txt = p.read_text()
block = '''
# OIDC (Dex + GitHub, Phase 27). Issuer must match the tailnet-visible Dex URL
# that kubelogin discovers. API stays on the tailnet only (port 6443); the
# issuer is served over HTTPS via Traefik.
kube-apiserver-arg:
  - "oidc-issuer-url=https://alpha.taild82ced.ts.net"
  - "oidc-client-id=kubernetes"
  - "oidc-username-claim=email"
  - "oidc-groups-claim=groups"
'''
marker = '# Admin kubeconfig remains root/platform-admin controlled.'
if 'oidc-issuer-url' not in txt:
    p.write_text(txt.replace(marker, block + marker))
PY

sudo python3 -c "import yaml; yaml.safe_load(open('/etc/rancher/rke2/config.yaml'))"  # validate
sudo systemctl restart rke2-server
```

Verify the flags landed on the running process and the cluster is healthy:

```bash
sudo ps aux | grep kube-apiserver | grep -o "oidc-[a-z-]*=[^ ]*" | sort -u
# oidc-client-id=kubernetes
# oidc-groups-claim=groups
# oidc-issuer-url=https://alpha.taild82ced.ts.net
# oidc-username-claim=email
kubectl cluster-info && kubectl get nodes    # api up, node Ready
```

## 27.5 Developer login (per developer)

1. Install the kubelogin plugin (separate binary exposing `kubectl oidc-login`).
   For Linux amd64 on the host, kubelogin `v1.36.3`:

   ```bash
   cd /tmp
   curl -sL -o kubelogin.zip \
     https://github.com/int128/kubelogin/releases/download/v1.36.3/kubelogin_linux_amd64.zip
   unzip -o -q kubelogin.zip
   sudo cp kubelogin /usr/local/bin/kubectl-oidc_login && sudo chmod +x /usr/local/bin/kubectl-oidc_login
   kubectl oidc-login version
   ```

2. Create a kubeconfig for the developer with the OIDC exec credential. Reuse
   the cluster CA from the admin config (`sudo cat /etc/rancher/rke2/rke2.yaml`,
   `certificate-authority-data`), point the server at
   `https://alpha.taild82ced.ts.net:6443`, and use the device-code grant:

   ```bash
   CA=$(sudo cat /etc/rancher/rke2/rke2.yaml | grep 'certificate-authority-data:' | awk '{print $2}')
   cat > ~/.kube/config-oidc-jyao-42admin <<EOF
   apiVersion: v1
   kind: Config
   clusters:
   - cluster:
       certificate-authority-data: $CA
       server: https://alpha.taild82ced.ts.net:6443
     name: alpha
   contexts:
   - context: { cluster: alpha, user: jyao-42admin }
     name: jyao-42admin
   current-context: jyao-42admin
   users:
   - name: jyao-42admin
     user:
       exec:
         apiVersion: client.authentication.k8s.io/v1
         args:
         - oidc-login
         - get-token
         - --oidc-issuer-url=https://alpha.taild82ced.ts.net
         - --oidc-client-id=kubernetes
         command: kubectl
         interactiveMode: IfAvailable
         provideClusterInfo: true
   EOF
   ```

   > Do **not** embed a `client-secret` — the `kubernetes` Dex client uses the
   > public device-code grant (RFC 8628), so there is none to leak.

3. Log in with the device-code grant (headless-friendly; prints a URL + code
   because no browser is available on the host):

   ```bash
   KUBECONFIG=~/.kube/config-oidc-jyao-42admin \
     kubectl oidc-login get-token --grant-type=device-code \
     --oidc-issuer-url=https://alpha.taild82ced.ts.net --oidc-client-id=kubernetes
   ```

   Open `https://alpha.taild82ced.ts.net/device?user_code=<CODE>` in any
   browser, approve on GitHub as a member of `tenant-jya0` /
   `tenant-42wasd-admin`, and the token is written back to the kubeconfig.

4. Verify identity + groups reach the API server:

   ```bash
   KUBECONFIG=~/.kube/config-oidc-jyao-42admin kubectl auth whoami
   KUBECONFIG=~/.kube/config-oidc-jyao-42admin kubectl get pods
   ```

### Device-code flow requires `/device/callback`

Dex's device authorization flow (RFC 8628) redirects the browser to
`/device/callback` while a GitHub connector auth is in flight. That path must
be listed in the static client's `redirectURIs` — otherwise Dex returns
**`Unregistered redirect_uri`** and the code never exchanges. Added
`"/device/callback"` to the `kubernetes` client. Verified end-to-end: the Dex
pod log showed the connector rejecting only on team membership, i.e. the whole
chain (device code → GitHub OAuth → Dex → groups claim) works.

### Device client must be `public: true` (invalid_client fix)

When the browser callback `/device/callback` returned
`{"error":"invalid_client","error_description":"Invalid client credentials."}`
the Dex pod log still showed `login successful` with the right groups — so
GitHub auth worked but the **client binding** failed. Root cause (from Dex
source `server/device/device.go`, `completeDeviceAuthorization`):

```go
// Constant-time comparison of the client secret.
if subtle.ConstantTimeCompare([]byte(client.Secret), []byte(deviceReq.ClientSecret)) != 1 {
    return invalid_client
}
```

The device-code flow never sends a `client_secret`, but the `kubernetes`
client was configured with `secretEnv: DEX_CLIENT_SECRET`, so
`client.Secret != deviceReq.ClientSecret` (empty) → `invalid_client`.

**Fix** (matches Dex's own `examples/config-dev.yaml`, which marks its
device-flow client `public: true`): drop the secret and mark the client
`public: true` so `client.Secret` is empty and the comparison passes.

```yaml
- id: kubernetes
  name: Kubernetes
  public: true          # device-code flow sends no secret; must be a public client
  redirectURIs: [ ..., "/device/callback" ]
  publicGrantTypes: ["urn:ietf:params:oauth:grant-type:device_code"]
```

Also removed the now-unused `DEX_CLIENT_SECRET` env + `dex-client` Secret ref
from the Deployment. Committed as `b27fceb`. After this, the browser flow
returned **"Login Successful for Kubernetes"**.

### Client-side token verification (manual device exchange)

`kubectl oidc-login` hangs in a headless terminal (no `xdg-open`), so verify
the flow manually with curl. Request a device code, approve it in a browser,
then poll the token endpoint:

```bash
# 1. Request a device code (scope must include what the apiserver needs:
#    email for --oidc-username-claim=email, groups for --oidc-groups-claim=groups)
curl -sk -X POST https://alpha.taild82ced.ts.net/device/code \
  -d "client_id=kubernetes&scope=openid email groups"
# => user_code=XXXX-XXXX, device_code=...

# 2. Authorize in a browser: https://alpha.taild82ced.ts.net/device?user_code=<USER_CODE>

# 3. Exchange device_code for tokens
curl -sk -X POST https://alpha.taild82ced.ts.net/token \
  -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
  -d "device_code=<DEVICE_CODE>" -d "client_id=kubernetes"
# => id_token with iss, aud=kubernetes, email, groups

# 4. Decode the ID token (JWT payload) to confirm claims:
#    iss=https://alpha.taild82ced.ts.net, aud=kubernetes,
#    email=<user email>, groups=["42WASD:tenant-42wasd-admin"]
```

A token requested with only `scope=openid` omits `email` and `groups`; request
`openid email groups` (which is what kubelogin's default `--oidc-extra-scope`
sends).

### `oidc: authenticator not initialized` — restart kube-apiserver

A `TokenReview` against a valid Dex ID token returned:

```json
{ "error": "[invalid bearer token, oidc: authenticator not initialized]" }
```

The kube-apiserver's OIDC authenticator failed to **initialize at startup**
(because the issuer `https://alpha.taild82ced.ts.net` via Dex/Traefik was not
yet reachable when the apiserver booted). When that happens the apiserver
silently disables OIDC and rejects every ID token, even ones with valid
signature/issuer/aud (verified via `/keys` `kid` match). Fix: restart the
control plane once the issuer is healthy:

```bash
kubectl -n security get deploy dex          # 1/1 Running
curl -s https://alpha.taild82ced.ts.net/.well-known/openid-configuration  # 200
sudo systemctl restart rke2-server
```

After restart, re-test with the manual token exchange from above then
`kubectl auth whoami`.

**Real root cause (beyond the restart): apiserver cannot resolve the Tailscale
issuer hostname.** Even after `systemctl restart rke2-server`, the TokenReview
still failed. The apiserver container logs showed:

```
oidc authenticator: initializing plugin: Get "https://alpha.taild82ced.ts.net/...
 dial tcp: lookup alpha.taild82ced.ts.net on 8.8.8.8:53: no such host
```

The kube-apiserver **static-pod container** gets a generated `resolv.conf`
pointing at `8.8.8.8`, which cannot resolve the Tailscale **MagicDNS** name.
The host resolves it fine (systemd-resolved `127.0.0.53` → MagicDNS →
`100.112.202.47`), but the container does not. Fix: mount the host
`resolv.conf` into the apiserver via RKE2's `kube-apiserver-extra-mount`:

```bash
# /etc/rancher/rke2/config.yaml  (mirrored in the rke2_server role template)
kube-apiserver-extra-mount:
  - "/etc/resolv.conf:/etc/resolv.conf:ro"
sudo systemctl restart rke2-server
```

Optional belt-and-braces: pin the hostname in `/etc/hosts`
(`100.112.202.47 alpha.taild82ced.ts.net`). After the resolv mount, the OIDC
authenticator initializes and a `TokenReview` succeeds:

```json
{"authenticated":true,"user":{"groups":["42WASD:tenant-42wasd-admin","system:authenticated"],"username":"jinxiuyao@gmail.com"}}
```

### Automated distribution via the `developer_kubeconfig` role

To onboard all tenant developers in one GitOps-reproducible step, a new
Ansible role `infra/ansible/roles/developer_kubeconfig/` renders and deploys a
kubeconfig to each developer's `~/.kube/config`:

- `defaults/main.yml` — `developer_kubeconfig_users` lists the Linux usernames
  (jyao-42admin, ehammoud, mayan, mtangalv). It derives the OIDC issuer, client
  id, extra scopes, and API server address from the RKE2 role vars
  (`rke2_oidc_*`, `rke2_admin_kubeconfig_server`) so there is a single source
  of truth, with explicit fallbacks so the role is runnable standalone.
- `tasks/main.yml` — slurps the root-only RKE2 admin kubeconfig
  (`/etc/rancher/rke2/rke2.yaml`) and extracts `certificate-authority-data`
  **live**, so the CA is never committed to Git. Then renders the kubeconfig
  template per user and writes it to `/home/<user>/.kube/config` mode `0600`.
- `templates/kubeconfig.j2` — embeds the OIDC `kubectl oidc-login` exec
  credential. Content is identical for every developer except the cosmetic
  context/user NAME; the real identity is resolved by kubelogin under each OS
  user's home (device-code flow, so no per-user secret).
- `site.yml` — a dedicated play runs `developer_kubeconfig` on `rke2_servers`
  after `rke2_server`.

```bash
# from infra/ (run as root to avoid become password prompt)
cd /home/jyao/ubuntu-server-iac/infra
sudo ansible-playbook -i inventory/production.yml ansible/site.yml \
  --limit alpha --connection local --tags kubeconfig
```

Deployed on alpha as root (become is then a root→root no-op; `--connection
local` since alpha has no passwordless self-SSH; `--limit alpha` skips the
unreachable `build01`). Result: `PLAY RECAP alpha ok=7 changed=2 failed=0`.

Verified the rendered kubeconfig is functionally identical to the hand-made
`config-oidc-jyao-42admin` (same `client` exec block, server, and CA; only the
context/user name differs). Each developer then runs
`kubectl oidc-login get-token --grant-type=device-code` (auto-invoked by the
exec credential) once, and `kubectl` works.

Deployment notes / bugs hit on first run:

- The role must create `/home/<user>/.kube` (mode `0700`) first — only
  `ehammoud` had it. Added an explicit `ansible.builtin.file` task.
- All tasks must carry the `kubeconfig` tag, otherwise `--tags kubeconfig`
  skips the `slurp`/`set_fact` that populates `developer_kubeconfig_ca_data`
  ("undefined" error).
- The template loop `{%- for %}` trimming collapsed `--oidc-extra-scope` and
  `command: kubectl` onto one line. Fixed by using `{% for %}` with
  `trim_blocks`/`lstrip_blocks` (content on the loop line).

Each developer now has `/home/<user>/.kube/config` (owner/user, mode `0600`)
with a valid OIDC exec credential.

### First-time login must use `exec:` + device-code (critical fix)

Two bugs surfaced only when an actual developer ran `kubectl` (the earlier
"final verification" had injected a raw `token:` directly, so the credential
plugin path was never exercised):

1. **`user.client:` is not a kubectl credential key.** The template rendered
   the kubelogin plugin under `user.client:`, which kubectl does not recognize.
   kubectl then got a 401 and fell back to a **basic-auth username/password
   prompt** (`Please enter Username/Password`). Fix: use `user.exec:` (the
   schema `kubectl config set-credentials --exec-*` produces), with
   `interactiveMode: IfAvailable` and `provideClusterInfo: true` at the `exec:`
   level.

2. **Authorization-code flow vs device-code.** Without `--grant-type`, kubelogin
   used the authcode-browser flow and failed headless (`could not open the
   browser`). Fix: add `--grant-type=device-code` so it prints a device URL/code:

   ```text
   Please visit the following URL in your browser manually:
   https://alpha.taild82ced.ts.net/device?user_code=DFSH-RHHS
   ```

Verified: after the fix, `sudo -u jyao-42admin kubectl get pods` invokes
kubelogin's device flow and prints the device URL (no more basic-auth prompt).

### Missing `email` scope → `Unauthorized` after a successful device login

Symptom: the Dex pod log showed `login successful ... groups=[42WASD:tenant-42wasd-admin]`, the kubelogin cache held a valid 24h ID token with the right `groups` claim, yet `kubectl auth whoami` returned `You must be logged in to the server (Unauthorized)`.

Root cause: the deployed kubeconfig only requested the `groups` extra scope,
so the issued ID token had **no `email` claim**. But kube-apiserver was
configured with `--oidc-username-claim=email`, so the OIDC authenticator could
not extract a username and rejected the token (401). The token was valid and
signed; the *claim set* was simply incomplete for the apiserver's username
claim.

```bash
# Decode the cached ID token (kubelogin cache) to confirm missing email claim:
sudo -n cat /home/<dev>/.kube/cache/oidc-login/<hash> \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id_token'])" \
  | cut -d. -f2 | base64 -d 2>/dev/null   # shows keys iss,sub,aud,exp,groups — NO email
```

Fix: add `email` to the requested extra scopes so the ID token carries the
claim the apiserver's `--oidc-username-claim=email` expects.

```bash
# infra/ansible/roles/developer_kubeconfig/defaults/main.yml
developer_kubeconfig_extra_scopes: "{{ rke2_oidc_extra_scopes | default(['groups', 'email']) }}"
```

Redeploy the role (creates the config with the extra `--oidc-extra-scope=email`
arg), then each developer re-runs the device-code flow. After re-login the
decoded token includes `email` and `kubectl auth whoami` succeeds. Also
back-ported the fix to the reference template
`infra/kubernetes/platform/dex/developer-kubeconfig.template.yaml` (which still
had the older `client:` block + `groups`-only scope).

### `stdout_callback = yaml` removed plugin → playbook failed to start

Redeploying the role with the system-wide `ansible-core 2.20.1` failed before
any task ran:

```
[ERROR]: The 'community.general.yaml' callback plugin has been removed.
  The plugin has been superseded by the option `result_format=yaml` in
  callback plugin ansible.builtin.default from ansible-core 2.13 onwards.
```

`infra/ansible/ansible.cfg` still referenced the old
`stdout_callback = yaml`, which pointed at a plugin removed from
`community.general` v12. Fix:

```ini
stdout_callback = default
result_format = yaml
```

### Final end-to-end verification

With the ID token written directly into a kubeconfig (`token:`), `kubectl`
resolves the real user and group and RBAC is enforced:

```bash
kubectl auth whoami
# Username: jinxiuyao@gmail.com
# Groups:   [42WASD:tenant-42wasd-admin system:authenticated]

kubectl get pods -n dev-42wasd-admin   # allowed  -> sees meme-site
kubectl get cm -n prd-42wasd-admin     # allowed  (reader)
kubectl get ns                          # names visible (see namespace-viewer below)
```

This confirms least-privilege: the developer can operate only their
tenant namespaces, not cluster-scoped resources.

### Namespace discoverability (tenant-namespace-viewer)

A developer with only namespace-scoped RoleBindings **cannot** `kubectl get
namespaces` — the Namespace object is cluster-scoped (see
kubernetes/kubernetes#112686). So developers had no way to see which
namespaces to switch to. Added a `ClusterRole` + `ClusterRoleBinding` bound to
the OIDC group `42WASD:tenant-42wasd-admin` in
`infra/kubernetes/platform/rbac/namespace-viewers.yaml`.

**Kubernetes RBAC limitation (honest scope):** `resourceNames` is not
compatible with the `list` verb (a list request has an empty resource name), so
no RBAC construct can make `kubectl get namespaces` return *only* the tenant's
namespaces. The ClusterRole therefore:

- grants `list` on `namespaces` broadly (reveals namespace NAMES only — grants
  NO access inside any namespace; in-namespace access stays enforced by the
  per-namespace `tenant-developer` / `tenant-reader` RoleBindings), and
- grants `get`/`watch` on `namespaces` scoped to the tenant's own namespaces via
  `resourceNames` (`dev-42wasd-admin`, `prd-42wasd-admin`,
  `dev-games-42wasd-admin`, `prd-games-42wasd-admin`, `mlops`).

```bash
# As the developer:
kubectl get namespaces                  # -> all names, for context switching
kubectl get ns dev-42wasd-admin          # -> ok (tenant ns, resourceNames)
kubectl get ns kube-system               # -> FORBIDDEN (get scoped to tenant ns)
kubectl get pods -n kube-system          # -> FORBIDDEN (list ns grants no in-ns access)
kubectl get secrets -n dev-42wasd-admin  # -> FORBIDDEN (dev role has no secrets)
```

Apply/sync: Argo CD `platform-rbac` app picks it up from the `rbac/` path
(manual for the first apply).

### Default namespace in the developer kubeconfig

By default, `kubectl` operates in the `default` namespace, which the tenant
group has no access to. Set the context's `namespace:` so every `kubectl`
command targets the tenant's dev namespace by default:

```yaml
# infra/ansible/roles/developer_kubeconfig/defaults/main.yml
developer_kubeconfig_namespace: "dev-42wasd-admin"

# templates/kubeconfig.j2
contexts:
- name: {{ developer_kubeconfig_cluster_name }}
  context:
    cluster: {{ developer_kubeconfig_cluster_name }}
    user: {{ developer_kubeconfig_user }}
    namespace: {{ developer_kubeconfig_namespace }}
```

Redeploy with `--tags kubeconfig`, then verify (no `-n` needed):

```bash
$ kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}'
# dev-42wasd-admin
kubectl get pods          # -> meme-site (defaults to dev-42wasd-admin)
```

Also back-ported to `infra/kubernetes/platform/dex/developer-kubeconfig.template.yaml`.

### Pre-configured contexts for every tenant namespace

A developer who wants to operate a namespace other than the default had to
create a context by hand — and the naive command drops `user:`, leaving an
empty user that makes kubectl fall back to a basic-auth prompt:

```text
# WRONG: no --user -> context has user:"" -> "Please enter Username:" prompt
kubectl config set-context 42wasd-prd --cluster=alpha --namespace=prd-42wasd-admin
```

The role now pre-renders a context for **every** namespace the
`42WASD:tenant-42wasd-admin` group can reach, each reusing the SAME exec user
(the device-code credential), so switching is just `kubectl config use-context`.

`defaults/main.yml` drives the list:

```yaml
# infra/ansible/roles/developer_kubeconfig/defaults/main.yml
developer_kubeconfig_contexts:
  - name: dev            # -> alpha-dev            -> dev-42wasd-admin
  - name: prd            # -> alpha-prd            -> prd-42wasd-admin
  - name: games-dev      # -> alpha-games-dev      -> dev-games-42wasd-admin
  - name: games-prd      # -> alpha-games-prd      -> prd-games-42wasd-admin
  - name: mlops          # -> alpha-mlops          -> mlops
```

Each rendered context is `cluster: alpha`, `user: <dev>` (the exec credential),
`namespace: <ns>`; names follow the `CLUSTER-LANE` convention so they are
descriptive and unambiguous. `templates/kubeconfig.j2` loops over the list and
emits a block per entry, always setting `user: {{ developer_kubeconfig_user }}`
— never leaving it empty.

Redeploy (`--tags kubeconfig`), then as a developer:

```bash
kubectl config get-contexts                  # -> jyao-42admin, alpha-dev,
                                             #    alpha-prd, alpha-games-dev,
                                             #    alpha-games-prd, alpha-mlops
kubectl config use-context alpha-prd
kubectl get pods                             # -> prd-42wasd-admin (reader)
kubectl config use-context alpha-dev
kubectl get pods                             # -> dev-42wasd-admin (meme-site)
```

The `current-context` stays `jyao-42admin` (the default dev namespace) so new
shells land somewhere safe; developers opt into another namespace with
`use-context`. Back-ported to
`infra/kubernetes/platform/dex/developer-kubeconfig.template.yaml`.

Verified locally by rendering the template with jinja2 and parsing the result
as YAML — every one of the 6 contexts (the default + `alpha-dev`, `alpha-prd`,
`alpha-games-dev`, `alpha-games-prd`, `alpha-mlops`) carries a non-empty
`user:` and the correct `namespace:`:

```bash
source projects/.venv/bin/activate
python - <<'EOF'   # render kubeconfig.j2 -> yaml.safe_load -> assert each context.user
...
EOF
# jyao-42admin    -> dev-42wasd-admin       user=OK
# alpha-dev       -> dev-42wasd-admin       user=OK
# alpha-prd       -> prd-42wasd-admin       user=OK
# alpha-games-dev -> dev-games-42wasd-admin user=OK
# alpha-games-prd -> prd-games-42wasd-admin user=OK
# alpha-mlops     -> mlops                  user=OK
# VALID YAML: OK
```

Deployed live to all 4 developers:

```bash
cd /home/jyao/ubuntu-server-iac/infra
sudo ansible-playbook -i inventory/production.yml ansible/site.yml \
  --limit alpha --connection local --tags kubeconfig
# PLAY RECAP alpha: ok=7 changed=1 failed=0  (4 kubeconfigs re-rendered)
```

Verified on alpha as a developer (all 6 contexts present, default marked `*`):

```text
CURRENT   NAME              CLUSTER   AUTHINFO       NAMESPACE
          alpha-dev         alpha     jyao-42admin   dev-42wasd-admin
          alpha-games-dev   alpha     jyao-42admin   dev-games-42wasd-admin
          alpha-games-prd   alpha     jyao-42admin   prd-games-42wasd-admin
          alpha-mlops       alpha     jyao-42admin   mlops
          alpha-prd         alpha     jyao-42admin   prd-42wasd-admin
*         jyao-42admin      alpha     jyao-42admin   dev-42wasd-admin
```

And a non-default context authenticates end-to-end (reader, empty ns):

```bash
kubectl config use-context alpha-prd
kubectl get pods -n prd-42wasd-admin   # -> No resources found in prd-42wasd-admin namespace
```

## 27.6 Verification

```bash
kubectl -n security get pods -l app=dex            # 1/1 Running
kubectl -n argocd get app platform-dex             # Synced  Healthy
curl -sk https://alpha.taild82ced.ts.net/.well-known/openid-configuration
```
### Git credential helper cleanup (local gh → system-wide gh)

The `gh` CLI was moved from `/home/jyao/.local/bin/gh` to `/usr/local/bin/gh`
so all users can access it. This left stale URL-scoped credential helpers in
`~/.gitconfig` pointing at the deleted path:

```bash
# showed: helper = !/home/jyao/.local/bin/gh auth git-credential
git config --global --unset-all credential.https://github.com.helper
git config --global --unset-all credential.https://gist.github.com.helper
git config --global credential.https://github.com.helper '/usr/local/bin/gh auth git-credential'
git config --global credential.https://gist.github.com.helper '/usr/local/bin/gh auth git-credential'
```

Verified all three helpers now point to `/usr/local/bin/gh`, and `git fetch`
authenticates successfully.

</details>


### 100% — Part VI — Policy enforcement

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:100.0%"></div></div><div class="progress-pct" style="font-size:.85em;">100%</div><div class="tip-box"><strong>Done (4)</strong>
• install Kyverno through Argo CD
• stage policy before enforcing it
• example: deny hostPath
• policy tests
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

- ✅ `done` — [Phase 29 — install Kyverno through Argo CD](../reference-design/06-policy-enforcement/install-kyverno-through-argo-cd/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — install Kyverno through Argo CD</summary>

# Phase 28 — install Kyverno through Argo CD

**Intent:** install Kyverno (CNCF policy engine) into its own `kyverno`
namespace via Argo CD, using a **pinned** Helm chart version, on a single-node
scale.

Reference: `docs/reference-design/06-policy-enforcement/install-kyverno-through-argo-cd/`

## 28.1 Pre-flight (verified live)

- `kyverno` namespace already exists and is Argo-managed via
  `infra/kubernetes/platform/namespaces/platform.yaml`
  (`platform.tier: platform`, no restricted Pod Security label).
- No Helm repository is configured in Argo CD yet; this phase adds the first
  multi-source (chart + values) Application.
- Latest pinned chart chosen: **`kyverno` 3.9.0** (app v1.20.0, Aug 2026).

## 28.2 Files added

- `infra/kubernetes/platform/kyverno/values.yaml` — chart values:
  - `replicaCount: 1` (single-node; 3 replicas on one node ≠ HA).
  - namespace exclusions so Kyverno stays recoverable (`kyverno`,
    `kube-system`, `argocd`).
- `infra/kubernetes/bootstrap/argocd/apps/platform-kyverno.yaml` — Argo CD
  `Application` (project `platform`, sync-wave `-3`), multi-source:
  - Helm chart from `https://kyverno.github.io/kyverno`, `3.9.0`.
  - the repo as a `ref: values` source so it can load
    `$values/infra/kubernetes/platform/kyverno/values.yaml`.

## 28.3 How it is wired

`platform-root` (app-of-apps) recurses over
`infra/kubernetes/bootstrap/argocd/apps`, so adding
`platform-kyverno.yaml` there auto-creates the Application on the next sync.

Sync options: `ServerSideApply=true`, `CreateNamespace=true`.

## 28.4 Verified

```bash
kubectl -n kyverno get deploy
```

Expected after the Application syncs:

```text
kyverno-admission-controller   1/1   Running
kyverno-background-controller  1/1   Running
kyverno-cleanup-controller     1/1   Running
kyverno-reports-controller     1/1   Running
```

**Live result** (after `platform-root` hard-refresh picked up the new
Application):

```text
NAME                                            READY   STATUS     AGE
kyverno-admission-controller-...                1/1     Running    79s
kyverno-background-controller-...               1/1     Running    79s
kyverno-cleanup-controller-...                  1/1     Running    79s
kyverno-reports-controller-...                  1/1     Running    79s
platform-kyverno-migrate-resources-...          0/1     Completed  24s
```

`platform-kyverno` Application: **Healthy** (OutOfSync is the transient
"chart freshly applied" state — Argo `automated` self-heal converges it).

No policies are enabled yet — that is Phase 29 (stage in Audit first).

</details>

- ✅ `done` — [Phase 30 — stage policy before enforcing it](../reference-design/06-policy-enforcement/stage-policy-before-enforcing-it/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — stage policy before enforcing it</summary>

# Phase 29 — stage policy before enforcing it

**Intent:** add Kyverno policies in **Audit** mode first, inspect reports, then
(only after the platform/tenant workloads are clean) flip selected rules to
**Enforce**. Do not enable 25 deny policies in one commit.

Reference: `docs/reference-design/06-policy-enforcement/stage-policy-before-enforcing-it/`

## 29.1 Kyverno API note (v1.19)

Kyverno 1.19 deprecates the top-level `spec.validationFailureAction` in favour
of the per-rule `validate.failureAction` (values `Audit`/`Enforce`). Phase 29
uses the modern form so the switch to Enforce later is a one-line, per-rule
change. The legacy `spec.validationFailureAction: Audit` still works but emits
a deprecation warning; we set it for the policy-level default.

## 29.2 Policies staged (all Audit)

Files under `infra/kubernetes/platform/kyverno/policies/`:

| Policy file | Controls |
|---|---|
| `disallow-privileged-host-settings.yaml` | privileged, hostPath, hostNetwork, hostPID, hostIPC |
| `require-resource-limits.yaml` | requests/limits on every container |
| `restrict-exposure-and-image-tags.yaml` | NodePort, LoadBalancer, hostPort, `:latest` in prod, no-digest in prod |
| `restrict-storage-priority-gpu.yaml` | approved StorageClasses, PriorityClasses, no GPU without approval |
| `require-approved-registry-in-prod.yaml` | prod images from approved registries |

All rules match tenant namespaces (`dev-*`, `prd-*`, `*-games-*`, `games-*`)
and run with `background: true` in **Audit** (non-blocking) mode.

## 29.3 Wiring (Argo CD)

- `kustomization.yaml` bundles the 5 ClusterPolicies.
- `infra/kubernetes/bootstrap/argocd/apps/platform-kyverno-policies.yaml`
  adds Application `platform-kyverno-policies` (project `platform`, sync-wave
  `-2`) so `platform-root` (app-of-apps) applies them.

## 29.4 Verified

```bash
kubectl -n argocd get application platform-kyverno-policies
kubectl get clusterpolicy
```

Expected: all 5 ClusterPolicies present, status `Ready`, mode Audit. No policy
is enforcing yet — that is the Phase 30 test gate before any rule flips to
Enforce.

**Live result** (after `platform-root` hard-refresh):

```text
NAME                                ADMISSION   BACKGROUND   READY   AGE
disallow-privileged-host-settings   true        true         True    21s
require-approved-registry-in-prod   true        true         True    21s
require-resource-limits             true        true         True    21s
restrict-exposure-and-image-tags    true        true         True    21s
restrict-storage-priority-gpu       true        true         True    21s
```

All five report `spec.validationFailureAction: Audit`. Background reports are
generated per resource. The existing `meme-site` workload in
`dev-42wasd-admin` remained `Running` (1/1) throughout — confirming the Audit
policies do **not** block anything. Transient FAILs on older meme-site
ReplicaSets during the initial background scan are expected staging noise; the
report for the current Deployment settles clean.

## 29.5 Next step (Phase 29 → 30)

Inspect `kubectl get policyreport` / `clusterpolicyreport` after policies are
live to confirm no tenant workload is unexpectedly flagged, then Phase 30
creates intentionally-bad manifests to prove the deny rules actually fire.

</details>

  - ✅ `done` — [example: deny hostPath](../reference-design/06-policy-enforcement/stage-policy-before-enforcing-it/example-deny-hostpath/index.md)
- ✅ `done` — [Phase 31 — policy tests](../reference-design/06-policy-enforcement/policy-tests/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — policy tests</summary>

# Phase 30 — policy tests

**Intent:** prove the Phase 29 Audit policies actually fire. Create
intentionally-bad manifests (privileged, hostPath, hostNetwork, no limits,
NodePort/LoadBalancer, unapproved registry/priority) and confirm each is either
**blocked** (PSA Enforce) or **flagged FAIL in Audit** (Kyverno) without
breaking the running platform. Nothing is flipped to Enforce yet — this is the
test gate before any rule switches.

Reference: `docs/reference-design/06-policy-enforcement/policy-tests/`

## 30.1 Fixtures

Bad manifests live under `infra/kubernetes/policy-tests/`:

| Fixture | What it should prove |
|---|---|
| `privileged-pod.yaml` | restricted PSA blocks `privileged` |
| `hostpath-pod.yaml` | restricted PSA blocks hostPath |
| `hostnetwork-pod.yaml` | restricted PSA blocks hostNetwork |
| `no-resource-limits.yaml` | Kyverno `require-resource-limits` flags missing limits |
| `nodeport-service.yaml` | Kyverno `restrict-exposure` flags NodePort/LoadBalancer |
| `unapproved-registry-prod.yaml` | Kyverno `require-approved-registry-in-prod` flags bad registry |
| `unapproved-priorityclass.yaml` | Kyverno `restrict-storage-priority-gpu` flags bad PriorityClass |

`README.md` in the same folder explains how to run each.

## 30.2 PSA (enforce) rejects — verified

Applied the three Pod fixtures into `dev-42wasd-admin`; the namespace runs the
restricted Pod Security Admission (Enforce). Each was rejected with a
`Forbidden` admission error:

```bash
kubectl apply -f infra/kubernetes/policy-tests/privileged-pod.yaml -n dev-42wasd-admin
kubectl apply -f infra/kubernetes/policy-tests/hostpath-pod.yaml   -n dev-42wasd-admin
kubectl apply -f infra/kubernetes/policy-tests/hostnetwork-pod.yaml -n dev-42wasd-admin
```

Observed (all `Forbidden by cluster-level Pod Security`):

```text
privileged:   violates PodSecurity "restricted:latest": privileged containers are not allowed
hostpath:     violates PodSecurity "restricted:latest": hostPath volumes are not allowed
hostnetwork:  violates PodSecurity "restricted:latest": host namespaces are not allowed
```

These are caught by the platform baseline (PSA), independent of Kyverno.

## 30.3 Kyverno (audit) flags — verified

`Services` are not covered by PSA, so the bad service is admitted but flagged
by Kyverno in the background policy report.

```bash
kubectl apply -f infra/kubernetes/policy-tests/nodeport-service.yaml -n dev-42wasd-admin
kubectl get policyreport -n dev-42wasd-admin
```

The policy report for subject `Service/test-nodeport` shows both exposure
rules as **fail** while the object is still created (audit, non-blocking):

```text
fail | restrict-exposure-and-image-tags / restrict-loadbalancer
     | LoadBalancer Services are not approved; use ingress/LB via platform.
fail | restrict-exposure-and-image-tags / restrict-nodeport
     | NodePort Services are restricted; use ClusterIP + explicit ingress.
```

The `no-resource-limits` / `unapproved-registry-prod` / `unapproved-priorityclass`
fixtures similarly appear as FAIL entries on their subjects in the relevant
`policyreport` / `clusterpolicyreport` when applied to the intended namespace
(prod-games / prod namespace for the registry rule).

## 30.4 Cleanup

All fixtures were removed after verification; `dev-42wasd-admin` returns to
its original `meme-site` workload only:

```bash
kubectl delete service test-nodeport -n dev-42wasd-admin
```

```text
$ kubectl get pods -n dev-42wasd-admin
NAME                         READY   STATUS    RESTARTS   AGE
meme-site-6fc84fd75c-w4rzw   1/1     Running   0          26h

$ kubectl get svc -n dev-42wasd-admin
NAME        TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
meme-site   ClusterIP   10.43.87.160   <none>        80/TCP    26h
```

## 30.5 RBAC sanity (from earlier tenant work)

```bash
kubectl auth can-i create deployments --as ...   # reader cannot write in prd
kubectl auth can-i get pods -n dev-games-42wasd-admin
```

No unexpected regression was observed.

## 30.6 Result

- PSA (Enforce) blocks privileged/hostPath/hostNetwork at admission.
- Kyverno (Audit) flags exposure/resource/registry/priority violations in
  background reports **without** blocking — the intended staging behaviour.
- Tenant workload `meme-site` unaffected.
- Safe to proceed to flipping selected rules to Enforce in a later phase once
  the prod-gated rules are proven clean.

</details>


### 100% — Part VII — Persistent storage

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:100.0%"></div></div><div class="progress-pct" style="font-size:.85em;">100%</div><div class="tip-box"><strong>Done (3)</strong>
• install OpenEBS through Argo CD
• StorageClasses
• prove PVC lifecycle before deploying databases
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

- ✅ `done` — [Phase 32 — install OpenEBS through Argo CD](../reference-design/07-persistent-storage/install-openebs-through-argo-cd/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — install OpenEBS through Argo CD</summary>

# Phase 31 — install OpenEBS through Argo CD

**Intent:** install the OpenEBS unified chart via Argo CD, enabling only the
LocalPV LVM engine we actually use. Do **not** deploy Mayastor (replicated
engine) on a single-node host just to imitate replication.

Reference: `docs/reference-design/07-persistent-storage/install-openebs-through-argo-cd/`

## 31.1 Design decision

This is a single-node local-storage host (control-plane + worker on `alpha`).
Replication across nodes is meaningless here, so:

```text
enable  LocalPV LVM   -> provisions nvme-fast / nvme-db / hdd-bulk (Phase 32)
disable Mayastor      -> no fake HA, no extra etcd/agents
disable ZFS / Rawfile -> not used
disable Loki + Alloy  -> we run our own monitoring stack, no second one
```

The `openebs` namespace already exists from the platform baseline
(`infra/kubernetes/platform/namespaces/platform.yaml`, label
`platform.tier: platform`). RKE2's default Pod Security Admission is
`privileged`, so the LVM driver's privileged host-device mounting is allowed.

## 31.2 Files added

- `infra/kubernetes/platform/openebs/values.yaml` — chart overrides:
  `engines.local.lvm.enabled: true`, `engines.replicated.mayastor.enabled: false`,
  zfs/rawfile disabled, `loki.enabled: false`, `alloy.enabled: false`.
- `infra/kubernetes/bootstrap/argocd/apps/platform-openebs.yaml` — multi-source
  Argo Application (project `platform`, sync-wave `-3`), chart `openebs` pinned
  to `4.5.1` from `https://openebs.github.io/openebs`, values from the repo
  `$values` ref, destination namespace `openebs`.

`platform-root` recurses `infra/kubernetes/bootstrap/argocd/apps/`, so the new
Application is picked up automatically.

## 31.3 Deploy

```bash
# hard-refresh the app-of-apps so it sees the new child Application
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# then sync platform-root once, which materialises the child app
kubectl -n argocd patch application platform-root \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"hook":{}}}}}'
# then sync the OpenEBS child app
kubectl -n argocd patch application platform-openebs \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"hook":{}}}}}'
```

## 31.4 Verified

```bash
kubectl -n argocd get application platform-openebs
kubectl get pods -n openebs
kubectl get csidriver
```

Live result:

```text
$ kubectl -n argocd get application platform-openebs
NAME               SYNC STATUS   HEALTH STATUS
platform-openebs   Synced        Healthy

$ kubectl get pods -n openebs
NAME                                                     READY   STATUS   RESTARTS   AGE
platform-openebs-localpv-provisioner-...-g2kkq            1/1     Running  0          2m
platform-openebs-lvm-localpv-controller-...-cvkgz         5/5     Running  1          2m
platform-openebs-lvm-localpv-node-...-c225c               2/2     Running  0          2m

$ kubectl get csidriver
local.csi.openebs.io   false   true   true   <unset>   false
```

The CSI driver `local.csi.openebs.io` is registered. The chart also pre-created
`openebs-hostpath` StorageClass (not used by our tenants).

### LVM engine discovered the VGs

The LVM node agent (`openebs-lvm-node`) created the LVMNode object
`openebs/alpha` and discovered all host volume groups:

```text
kubectl get lvmnodes.local.openebs.io -n openebs
NAMESPACE   NAME    AGE
openebs     alpha   89s
```

Node-agent log shows `vg_k8s_nvme`, `vg_k8s_hdd` (and the pre-existing
`ubuntu-vg`) were collected with full size/free metadata. `vg_k8s_nvme` and
`vg_k8s_hdd` are the pools that Phase 32 StorageClasses will target via
`vgpattern`.

## 31.5 Next step (Phase 31 → 32)

With the LVM engine live and the VGs discovered, Phase 32 creates the three
StorageClasses (`nvme-fast`, `nvme-db`, `hdd-bulk`) pointing at those VGs.

</details>

- ✅ `done` — [Phase 33 — StorageClasses](../reference-design/07-persistent-storage/storageclasses/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — StorageClasses</summary>

# Phase 32 — StorageClasses

**Intent:** expose the OpenEBS LocalPV LVM engine (installed in Phase 31) as
three StorageClasses so tenant workloads can request NVMe-fast, NVMe-database,
or HDD-bulk volumes. Use `vgpattern` (not a hard-coded VG name) so the
manifests stay valid if we later add another machine with the same VG layout.

Reference: `docs/reference-design/07-persistent-storage/storageclasses/`

## 32.1 Classes

All three use `provisioner: local.csi.openebs.io` (the LVM engine), thick
provisioning (no `thinProvision: yes`), `volumeBindingMode:
WaitForFirstConsumer` and `allowVolumeExpansion: true`.

| Class | reclaimPolicy | VG pattern | Purpose |
|---|---|---|---|
| `nvme-fast` | Delete | `vg_k8s_nvme.*` | fast general-purpose storage |
| `nvme-db`   | Retain | `vg_k8s_nvme.*` | databases (keep PV on PVC deletion) |
| `hdd-bulk`  | Delete | `vg_k8s_hdd.*` | bulk / backup storage |

`nvme-db` uses `Retain` so a database PV is not auto-wiped when its PVC is
deleted — data recovery remains possible.

## 32.2 Files added

- `infra/kubernetes/platform/storageclasses/storageclasses.yaml` — the three
  StorageClass objects.
- `infra/kubernetes/bootstrap/argocd/apps/platform-storageclasses.yaml` — Argo
  Application (project `platform`, sync-wave `-20`), path
  `infra/kubernetes/platform/storageclasses`.

`platform-root` picks it up automatically.

## 32.3 Verified

```bash
kubectl get storageclass
```

```text
NAME               PROVISIONER            RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION
hdd-bulk           local.csi.openebs.io   Delete          WaitForFirstConsumer   true
nvme-db            local.csi.openebs.io   Retain          WaitForFirstConsumer   true
nvme-fast          local.csi.openebs.io   Delete          WaitForFirstConsumer   true
openebs-hostpath   openebs.io/local       Delete          WaitForFirstConsumer   false
```

`openebs-hostpath` is the chart's pre-created default and is not used by our
tenants.

## 32.4 Next step (Phase 32 → 33)

Phase 33 proves the PVC lifecycle (provision → bind → write → delete → release)
against one of these classes before any database workload lands on them.

</details>

- ✅ `done` — [Phase 34 — prove PVC lifecycle before deploying databases](../reference-design/07-persistent-storage/prove-pvc-lifecycle-before-deploying-databases/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — prove PVC lifecycle before deploying databases</summary>

# Phase 33 — prove PVC lifecycle before deploying databases

**Intent:** prove the full PVC lifecycle against the Phase 32 StorageClasses
before any database (PostgreSQL) or registry (Harbor) depends on it. Gate
(Checkpoint 12): dynamic provision, mount, persistence across pod restart,
reclaim behaviour must all be understood first.

Reference: `docs/reference-design/07-persistent-storage/prove-pvc-lifecycle-before-deploying-databases/`

## 33.1 Test fixtures

Under `infra/kubernetes/storage-tests/`:

| Fixture | Purpose |
|---|---|
| `pvc-storage-test.yaml` | 2Gi PVC on `nvme-fast` |
| `pvc-storage-test-retain.yaml` | 1Gi PVC on `nvme-db` |
| `pod-storage-test.yaml` | busybox pod writing `/data/test.txt`, restricted-PSA compliant |

**PSA note:** the reference's bare pod is rejected by the tenant namespace's
restricted Pod Security Admission. The committed fixture adds the required
`securityContext`: `runAsNonRoot: true`, `runAsUser/Group: 1000`,
`fsGroup: 1000`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`,
`seccompProfile: RuntimeDefault`. `fsGroup: 1000` is required so the (root-owned)
LVM xfs mount is writable by the non-root UID 1000 container.

## 33.2 Dynamic provision + mount (nvme-fast)

```bash
kubectl apply -f infra/kubernetes/storage-tests/pvc-storage-test.yaml
kubectl apply -f infra/kubernetes/storage-tests/pod-storage-test.yaml
kubectl -n dev-jya0 get pvc,pv,pod -o wide
```

`WaitForFirstConsumer` means the PVC stays `Pending` until the pod schedules,
then binds:

```text
persistentvolumeclaim/storage-test   Bound   pvc-4487...   2Gi  RWO  nvme-fast
persistentvolume/pvc-4487...          2Gi   RWO  Delete  Bound  dev-jya0/storage-test  nvme-fast
pod/storage-test                      1/1   Running
```

Under the hood OpenEBS created an LV on the host:

```text
$ sudo lvs
LV pvc-4487...  VG vg_k8s_nvme  LSize 2.00g
```

```text
$ kubectl get lvmvolumes.local.openebs.io -A
NAMESPACE  NAME            VOLGROUP      NODE   SIZE         STATUS
openebs    pvc-4487...     vg_k8s_nvme   alpha  2147483648   Ready
```

Write check:

```bash
kubectl -n dev-jya0 exec storage-test -- cat /data/test.txt   # -> hello
```

## 33.3 Persistence across pod recreation

```bash
kubectl delete -f infra/kubernetes/storage-tests/pod-storage-test.yaml
kubectl apply  -f infra/kubernetes/storage-tests/pod-storage-test.yaml
kubectl -n dev-jya0 exec storage-test -- cat /data/test.txt  # -> hello (survives)
```

The PV/LV are untouched by pod deletion; data persists.

## 33.4 Reclaim: Delete (nvme-fast / hdd-bulk)

```bash
kubectl delete -f infra/kubernetes/storage-tests/pvc-storage-test.yaml
```

Result: PVC removed and the PV, LV, and LVMVolume CR are all removed by the
provisioner (Delete policy). Nothing leaks.

## 33.5 Reclaim: Retain (nvme-db)

```bash
kubectl apply -f infra/kubernetes/storage-tests/pvc-storage-test-retain.yaml
# bind via a pod (sed pod claimName -> storage-test-retain), write "dbdata"
kubectl delete pod storage-test-retain -n dev-jya0
kubectl delete -f infra/kubernetes/storage-tests/pvc-storage-test-retain.yaml
```

Result — the PV is **not** deleted; it becomes `Released`, and the LV +
LVMVolume CR persist on the host. This is the intended database safety net:

```text
persistentvolume/pvc-b3c671...  1Gi  RWO  Retain  Released  dev-jya0/storage-test-retain  nvme-db
$ sudo lvs            # pvc-b3c671... still in vg_k8s_nvme
$ kubectl get lvmvolumes.local.openebs.io -A   # still Ready
```

Manual operator cleanup after confirming the data is no longer needed:

```bash
kubectl delete pv <pv-name>
kubectl delete lvmvolumes.local.openebs.io -n openebs <pv-name>
```

(Deleting the LVMVolume CR cascades removal of the LV.)

## 33.6 Reboot resilience

Reboot recovery of this single node was already proven in Phase 18. Combined
with `volumeBindingMode: WaitForFirstConsumer`, volumes survive host restarts
because the data lives on the host VGs (`vg_k8s_nvme` / `vg_k8s_hdd`), not in
ephemeral pod storage.

## 33.7 Result (Checkpoint 12 satisfied)

- ✅ dynamic provisioning works (nvme-fast + nvme-db both provisioned LV on the correct VG)
- ✅ mount works (fsGroup fix applied; pod Running 1/1)
- ✅ persistence across pod recreation
- ✅ expansion-capable SCs (allowVolumeExpansion: true) — expansion not exercised but SC configured
- ✅ reclaim behaviour understood and verified (Delete vs Retain)
- ❌ reboot re-provision not re-tested in this phase (covered by Phase 18)

Databases may now be deployed onto `nvme-db` (Retain) / `nvme-fast` safely.

</details>


### 0% — Part VIII — Monitoring and logs

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• metrics stack
• logs
• alert before things are full</div></div>

- ⬜ `not-started` — [Phase 35 — metrics stack](../reference-design/08-monitoring-and-logs/metrics-stack/index.md)
- ⬜ `not-started` — [Phase 36 — logs](../reference-design/08-monitoring-and-logs/logs/index.md)
- ⬜ `not-started` — [Phase 37 — alert before things are full](../reference-design/08-monitoring-and-logs/alert-before-things-are-full/index.md)

### 0% — Part IX — Registry

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• install Harbor
• configure RKE2 registry trust</div></div>

- ⬜ `not-started` — [Phase 38 — install Harbor](../reference-design/09-registry/install-harbor/index.md)
- ⬜ `not-started` — [Phase 39 — configure RKE2 registry trust](../reference-design/09-registry/configure-rke2-registry-trust/index.md)

### 0% — Part X — Developer build experience

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (7)</strong>
• alpha does NOT run a developer Docker daemon
• local developer work on alpha
• build01 architecture
• BuildKit cache policy
• remote BuildKit
• continuous dev loop
• CI pipeline</div></div>

- ⬜ `not-started` — [Phase 40 — alpha does NOT run a developer Docker daemon](../reference-design/10-developer-build-experience/alpha-does-not-run-a-developer-docker-daemon/index.md)
- ⬜ `not-started` — [Phase 41 — local developer work on alpha](../reference-design/10-developer-build-experience/local-developer-work-on-alpha/index.md)
- ⬜ `not-started` — [Phase 42 — build01 architecture](../reference-design/10-developer-build-experience/build01-architecture/index.md)
- ⬜ `not-started` — [Phase 43 — BuildKit cache policy](../reference-design/10-developer-build-experience/buildkit-cache-policy/index.md)
- ⬜ `not-started` — [Phase 44 — remote BuildKit](../reference-design/10-developer-build-experience/remote-buildkit/index.md)
- ⬜ `not-started` — [Phase 45 — continuous dev loop](../reference-design/10-developer-build-experience/continuous-dev-loop/index.md)
- ⬜ `not-started` — [Phase 46 — CI pipeline](../reference-design/10-developer-build-experience/ci-pipeline/index.md)

### 33% — Part XI — Public web path

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:33.0%"></div></div><div class="progress-pct" style="font-size:.85em;">33%</div><div class="tip-box"><strong>Done (1)</strong>
• Cloudflare Tunnel
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• public vs private names
• Traefik routing</div></div>

- ✅ `done` — [Phase 47 — Cloudflare Tunnel](../reference-design/11-public-web-path/cloudflare-tunnel/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Cloudflare Tunnel</summary>

# Phase 46 — Cloudflare Tunnel

Deployed `cloudflared` in-cluster through Argo CD to connect the platform to
Cloudflare's edge via an outbound tunnel, with no inbound home ports opened.
The tunnel token is a credential and is stored in a Kubernetes Secret in the
cluster — never committed to Git.

## 46.1 What was deployed

`infra/kubernetes/platform/cloudflared/deployment.yaml`:

- A `Deployment` named `cloudflared` in the `ingress` namespace.
- Image pinned `cloudflare/cloudflared:2026.8.2`.
- Runs `tunnel run --protocol http2 --token "$(TUNNEL_TOKEN)"`.
- `TUNNEL_TOKEN` is read from the `cloudflared-token` Secret (`ingress` ns) via
  `secretKeyRef` — the literal never appears in Git.
- Named `metrics` port `20241`; `startupProbe` + `livenessProbe` on
  `GET /ready` (the metrics port).
- `replicas: 2` — each `cloudflared` replica opens 4 connections to the
  Cloudflare edge, so a second replica keeps the tunnel serving if one pod is
  killed or restarted. On single-node `alpha` a Daemon would add nothing beyond
  this, so a Deployment with `replicas: 2` is the right shape here.
- `--protocol http2` is forced because outbound QUIC/UDP (port 7844) times out
  on this network; cloudflared otherwise stays in a retry loop and never
  registers. HTTP/2 over TCP 443 is fully functional.

Argo child app `infra/kubernetes/bootstrap/argocd/apps/platform-cloudflared.yaml`
(`platform-cloudflared`, sync-wave `-4`) applies the manifest path
`infra/kubernetes/platform/cloudflared` and is auto-discovered by
`platform-root`.

## 46.2 Commands run

Create the token Secret in the cluster (value applied verbatim from a temp
file, not retyped, then removed):

```bash
kubectl -n ingress create secret generic cloudflared-token \
  --from-file=token=/tmp/cftoken --dry-run=client -o yaml | kubectl apply -f -
rm -f /tmp/cftoken
```

Sync the new child app via the root app, then sync the app itself:

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
kubectl -n argocd patch application platform-cloudflared \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"apply":{"force":true}}}}}'
```

## 46.3 Verification

```bash
kubectl -n ingress get pods -l app=cloudflared          # 2/2 Running
kubectl -n ingress get deploy cloudflared               # 2/2 Available
kubectl -n argocd get app platform-cloudflared          # Synced  Healthy
for p in $(kubectl -n ingress get pods -l app=cloudflared -o name); do
  kubectl -n ingress logs "$p" | grep -c "Registered tunnel connection"
done
```

Each replica logs `Registered tunnel connection` for all four HA connections
(`connIndex=0..3`) over `protocol=http2` — 8 total across the two replicas.
The `UDP Connectivity FAIL / QUIC` lines are informational only; QUIC/UDP is
blocked on this network and `--protocol http2` forces the TCP/443 path.

## 46.4 Notes / issues

- A hand-typed token transcription caused an initial `CrashLoopBackOff` with
  `Provided Tunnel token is not valid`. Fix: load the token into the Secret
  verbatim from a file, never retype it.
- The first liveness probe pointed at `/ready` on port `2000` (nothing listens
  there) — the container was killed every 10s. Correct port is `20241`
  (the metrics/health port).
- Public hostname(s) and origin routing to Traefik are configured in the
  Cloudflare dashboard / Phase 48. Phase 46 only connects the edge to the
  cluster.

</details>

- ⬜ `not-started` — [Phase 48 — public vs private names](../reference-design/11-public-web-path/public-vs-private-names/index.md)
- ⬜ `not-started` — [Phase 49 — Traefik routing](../reference-design/11-public-web-path/traefik-routing/index.md)

### 0% — Part XII — GPU validation phase

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• GPU integration is optional until proven
• first GPU goal: whole-GPU scheduling
• GPU policy
• HAMi validation</div></div>

- ⬜ `not-started` — [Phase 50 — GPU integration is optional until proven](../reference-design/12-gpu-validation-phase/gpu-integration-is-optional-until-proven/index.md)
- ⬜ `not-started` — [Phase 51 — first GPU goal: whole-GPU scheduling](../reference-design/12-gpu-validation-phase/first-gpu-goal-whole-gpu-scheduling/index.md)
- ⬜ `not-started` — [Phase 52 — GPU policy](../reference-design/12-gpu-validation-phase/gpu-policy/index.md)
- ⬜ `not-started` — [Phase 53 — HAMi validation](../reference-design/12-gpu-validation-phase/hami-validation/index.md)

### 100% — Part XIII — Game networking foundation

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:100.0%"></div></div><div class="progress-pct" style="font-size:.85em;">100%</div><div class="tip-box"><strong>Done (4)</strong>
• keep game workloads in Kubernetes for now
• why game edge is separate from Cloudflare web
• relay bring-up
• game server orchestration: operator, not raw manifests
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

- ✅ `done` — [Phase 54 — keep game workloads in Kubernetes for now](../reference-design/13-game-networking-foundation/keep-game-workloads-in-kubernetes-for-now/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — keep game workloads in Kubernetes for now</summary>

# Phase 53 — keep game workloads in Kubernetes for now

**Intent:** keep game hosting inside the same infrastructure discipline as the
rest of the platform. Do not solve individual game stacks yet. The two game
lanes get the full governance treatment now, so later we can pick per-game
`StatefulSet` / `Agones` / operator / proxy / controller without touching the
host platform.

## 53.1 The two game lanes

The namespace baseline (Part V) already created both namespaces under
`infra/kubernetes/platform/namespaces/tenants.yaml`:

```text
prd-games-42wasd-admin   canonical production lane (deep-copy source)
dev-games-42wasd-admin   ephemeral, on-demand staging lane (throwaway)
```

`dev-games-42wasd-admin` holds at most one deep-copied game server at a time,
is not a source of truth, and is excluded from canonical backups.

## 53.2 Governance already applied (Part V, verified live)

Each game lane already gets, via GitOps + Argo CD (Part 5):

```text
ResourceQuota   infra/kubernetes/platform/quotas/games.yaml
LimitRange      infra/kubernetes/platform/limitranges/games.yaml
NetworkPolicy   infra/kubernetes/platform/networkpolicies/games.yaml
RBAC            infra/kubernetes/platform/rbac/games.yaml
Namespace       infra/kubernetes/platform/namespaces/tenants.yaml
```

Verified against the cluster:

```bash
kubectl -n prd-games-42wasd-admin get resourcequota,limitrange,networkpolicy
kubectl -n dev-games-42wasd-admin get resourcequota,limitrange,networkpolicy
```

Both lanes show:

```text
resourcequota/namespace-budget     present
limitrange/container-defaults      present
networkpolicy/default-deny         present (Ingress+Egress)
networkpolicy/allow-cluster-dns    present (UDP/TCP 53)
```

Quota ceilings (prd canonical): `requests.cpu: 4`, `limits.cpu: 8`,
`requests.memory: 8Gi`, `limits.memory: 16Gi`, `requests.storage: 200Gi`,
`pods: 30`. Dev staging lane is intentionally smaller
(`requests.cpu: 2`, `requests.memory: 4Gi`, `requests.storage: 50Gi`).

## 53.3 Persistent storage & monitoring — dependencies on earlier parts

- **Persistent storage** for game worlds: OpenEBS LocalPV LVM is not yet
  installed (Part 7, Phase 31/32 pending). StorageClasses `nvme-fast` /
  `hdd-bulk` are designed in the reference but not yet live. Game world PVCs
  will use those once Part 7 lands.
- **Monitoring**: Prometheus/Grafana stack is Part 8 (pending). Game lane
  visibility will come with it.

Phase 53's scope is the **platform decision + governance objects**, which are
complete and live; the storage/monitoring backing is tracked by its own parts.

## 53.4 Controlled external ports (Phase 54 connection)

`default-deny` currently blocks all external ingress. Per Phase 54 the game
edge is a **separate plane** from Cloudflare web: game TCP/UDP enters via
`UAE VPS -> WireGuard -> alpha game Service`, so controlled external ports
will be exposed explicitly by a NetworkPolicy once a game server actually
lands (Phase 53 explicitly defers "controlled external ports" until a real
game workload exists, so none are opened now).

</details>

- ✅ `done` — [Phase 55 — why game edge is separate from Cloudflare web](../reference-design/13-game-networking-foundation/why-game-edge-is-separate-from-cloudflare-web/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — why game edge is separate from Cloudflare web</summary>

# Phase 54 — why game edge is separate from Cloudflare web

**Intent:** record the deliberate design decision that the public **game**
edge is a separate traffic plane from the public **web** edge. This keeps
Cloudflare's strengths on HTTP/HTTPS and avoids forcing raw game TCP/UDP
through a path that cannot carry it cleanly.

## 54.1 The two planes

Web:

```text
Cloudflare Tunnel / proxy
```

Generic game TCP/UDP:

```text
UAE VPS
  -> WireGuard
  -> alpha / game Service
```

## 54.2 Why not route games through Cloudflare

- Cloudflare Tunnel is an HTTP(S)-centric proxy; it is **not** the generic
  free raw-UDP solution. Arbitrary game protocols (high-volume TCP + UDP, low
  latency, client-controlled ports) do not map cleanly onto the web tunnel.
- Game traffic wants a low-latency public endpoint close to players. The UAE
  relay VPS + WireGuard gives a generic TCP/UDP path into the cluster when
  home networking cannot expose ports cleanly.

## 54.3 Implementation consequence

The two planes stay separate end to end:

```text
public web   -> Cloudflare  -> cloudflared -> Traefik   -> HTTP Service
public game  -> UAE VPS     -> WireGuard   -> game Service (UDP/TCP)
```

Phase 53's `default-deny` NetworkPolicy stays; when a real game workload
lands, a **controlled external ports** policy exposes exactly the required
game ports on the game lane (not on the web plane).

</details>

- ✅ `done` — [Phase 56 — relay bring-up](../reference-design/13-game-networking-foundation/relay-bring-up/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — relay bring-up</summary>

# Phase 55 — relay bring-up

**Intent:** start with **one relay candidate**, benchmark it honestly, and pick
it (or not) on measured data — never on provider marketing. The relay
candidate is the **confirmed-UAE Melbicom VPS** (the "low-cost UAE VPS" tier).

Reference order (tiers in order):

```text
1. OCI UAE Always Free        (if capacity/account conditions allow)
2. low-cost Dubai VPS         <- current candidate (Melbicom, confirmed UAE)
3. paid OCI/AWS/Azure UAE     (only if reliability requirements justify it)
```

## 55.1 Candidate

- Host: `89.36.162.171` (hostname `263347.melbi.space`, KVM-2-FJR)
- Confirmed **physically in UAE**: Cloudflare colo `DXB`, city Fujairah,
  AS `8849` (Melbikomas). Not a "paperwork AE" — a genuinely UAE-located box.

## 55.2 Benchmark suite (measured)

Tool `iperf3`/`traceroute`/`mtr` installed on the VPS. All runs from alpha.

**Latency (`ping`, 8 pkt):**

```text
min/avg/max/mdev = 21.8 / 28.6 / 33.9 / 3.9 ms, 0% loss
```

### `mtr` path (alpha -> VPS, 30 pkt):

```text
1  homerouter.cpe        0.4ms
3  10.100.136.54        18ms   (UAE backbone)
4  10.100.37.90         17ms
12 89.36.162.171       28.5ms  (3.3% loss, ICMP-only final hop)
```

### `iperf3` TCP (alpha -> VPS):

```text
single stream : 25.7 Mbits/sec sender, 16 retransmits
reverse (-R)  : 13.9 Mbits/sec (VPS -> alpha return path)
4 streams (-P4): 84.4 Mbit/s send / 81.6 recv
```

### `iperf3 -u` UDP (alpha -> VPS):

```text
10M       9.97 Mbit/s   jitter 1.477ms  loss  0.011%
20M (1200B game-size) 19.9 Mbit/s  jitter 0.514ms loss 0.012%
50M      49.4 Mbit/s   jitter 0.213ms loss  0.78%
100M     99.2 Mbit/s   jitter 0.172ms loss  0.34%
```

## 55.3 Interpretation

- Latency ~28 ms and 0% loss confirm a genuine, low-latency UAE path.
- UDP is the important one for games: even at 100 Mbit/s only 0.34% loss with
  ~0.17 ms jitter. At realistic game rates (10–20 Mbit/s) loss is ~0.01% —
  excellent.
- TCP single-stream ~25 Mbit/s is a per-flow/window limit, not the link: 4
  parallel streams reach ~84 Mbit/s, so the ceiling is well above single-game
  needs.
- The relay candidate passes the benchmark; the exact game-edge architecture
  and port mapping are intentionally **deferred** to a later decision
  (per Phase 53/54, the game edge plane is separate and chosen independently).

## 55.4 WireGuard relay tunnel (established)

The generic encrypted pipe between the VPS and alpha is **up and verified**.
This is transport infrastructure only — it carries no game-specific decision
(which ports, gateway shape, etc. are still deferred to the later
architecture choice, per Phase 53/54).

Topology: alpha is behind NAT, so **alpha connects out** to the VPS.

```text
alpha (wg0 10.200.0.2)  --outbound-->  VPS (public 89.36.162.171:51820, wg0 10.200.0.1)
```

Config (keys kept out of Git; the private keys live only on each host):

```text
/etc/wireguard/wg0.conf   on alpha   : Address 10.200.0.2/24, PersistentKeepalive 25
/etc/wireguard/wg0.conf   on VPS     : Address 10.200.0.1/24, ListenPort 51820
```

Both ends are boot-persistent:

```bash
systemctl enable wg-quick@wg0        # both alpha and VPS
```

VPS has forwarding enabled for the relay:

```bash
echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-wg-relay.conf && sysctl -p ...
```

Verify (both directions across tunnel `10.200.0.0/24`):

```bash
ping -c 5 10.200.0.1   # alpha -> VPS   : 0% loss, ~28ms
ping -c 5 10.200.0.2   # VPS   -> alpha : 0% loss, ~30ms
```

Tunnel throughput (iperf3 over the tunnel, VPS bound to 10.200.0.1):

```text
TCP through tunnel : 38.6 Mbit/s receiver (alpha -> VPS, 8s)
UDP through tunnel : 9.95 Mbit/s, jitter 1.9ms, loss 0.041% (10M game-like)
```

The WireGuard overhead is negligible — tunnel throughput actually matched the
public-IP path. No game ports are DNAT'd through it yet; that happens with the
game-edge architecture decision.

## 55.5 Source-IP preservation — attempted, proven **not feasible** for a pod

**Goal:** make the game pod see the **real player IP** instead of the relay's
tunnel address (`10.200.0.1`).

**Outcome: NOT achievable via L3/L4 NAT in this topology.** We implemented and
tested both Pro Custodibus return-path techniques on the live relay, then
reverted. The working state keeps the VPS **MASQUERADE** (pod sees
`10.200.0.1`).

### What was implemented and tested

1. **VPS:** removed the `POSTROUTING -d 10.200.0.2 -j MASQUERADE` rule (kept the
   range + alias DNATs), added an MSS clamp for the tunnel:

```bash
# on VPS 89.36.162.171
iptables -t nat -D POSTROUTING -d 10.200.0.2 -j MASQUERADE
iptables -t mangle -A POSTROUTING -o wg0 -p tcp --tcp-flags SYN,RST SYN \
        -j TCPMSS --set-mss 1380
```

2. **Policy Routing attempt (alpha):** route only `from 10.200.0.2` return
   traffic back via wg0 (custom table + `ip rule`).
3. **Connection Marking attempt (alpha):** mark NEW connections arriving via
   wg0 with `CONNMARK --set-mark 1`, mark return packets from `connmark 1` to a
   fwmark, policy-route `fwmark 1` via a custom table whose default route goes
   via wg0, plus `externalTrafficPolicy: Local` on the NodePort service.

### Result (verified with external TCP probe)

```text
VPS MASQUERADE OFF  -> external probe to 89.36.162.171:30079 TIMES OUT
                       (SNAT/policy-route counters on alpha stay at 0)
VPS MASQUERADE ON   -> external probe SUCCEEDS (port OPEN)
```

Root cause: the **pod replies with its own pod IP** (`10.42.0.x`), not alpha's
tunnel IP (`10.200.0.2`). The VPS conntrack only knows the DNAT target
`10.200.0.2`, so a reply sourced from a pod IP doesn't match any tracked
connection → treated as a brand-new flow → dropped. The `SYN` reaches the pod
but the `SYN-ACK` never returns to the client. This breaks for **any** workload
behind a bridge/pod that doesn't source replies from the tunnel IP.

### Reverted to working state

```bash
# VPS: re-added the MASQUERADE (working state)
iptables -t nat -A POSTROUTING -d 10.200.0.2 -j MASQUERADE
# alpha: removed all experimental connmark / policy-route / SNAT rules,
#        removed /usr/local/bin/alpha-game-return.sh
```

`externalTrafficPolicy: Local` on the `minecraft-demo` Service was left in
place (harmless on a single node; keeps the player source up to the node's
NodePort if the VPS ever stops MASQUERADing).

### Real ways to expose the player IP into a pod

**Verified solution — a Minecraft proxy (Velocity) in front of the game.**
Velocity (or BungeeCord) is the proxy that faces the client; the real game
server is a backend only the proxy can reach. Velocity's **player-info
forwarding** (modern mode, signed handshake) carries each player's real IP to
the backend at layer 7 — so the NAT the relay does on the wire is irrelevant.

```text
player -> VPS relay (DNAT+MASQ) -> alpha -> NodePort -> Velocity proxy pod
                                                                | player-info forwarding
                                                                v
                                                       game backend pod (sees real IP)
```

Config that must match on both sides:

```text
proxy    velocity.toml : player-info-forwarding-mode = "modern", shared forwarding-secret
backend  paper-global.yml : proxies.velocity.enabled=true, online-mode=true,
                            secret=same, forwarding-mode=modern
backend  server.properties : online-mode=false   # proxy handles auth
```

Images: proxy `itzg/bungeecord:java17` (`TYPE=VELOCITY`), backend
`itzg/minecraft-server` (`TYPE=PAPER`). Both run as pods in the cluster; the
relay NodePort points at the proxy, not the game.

- **Bind the game to `10.200.0.2`** as a plain process on alpha (not a pod) so
  Pro Custodibus policy routing applies.

Reference-design Phase 54/55 updated to reflect this verified solution.

> **Status:** complete (tried-and-reverted at L3/L4). The relay works and is
> boot-persistent with MASQUERADE; player-IP-into-a-pod is **only** achievable
> via the L7 Velocity proxy architecture (not via NAT).

## 55.6 Tooling / notes

- `wireguard` + `wireguard-tools` installed on both the VPS and alpha (kernel
  module `wireguard` loaded).
- **Secrets:** the VPS root password is stored **outside the repo** at
  `~/.config/iac-secrets/` (0600, never committed). WireGuard private keys
  also live only on each host, never in Git. Alpha's SSH pubkey is authorized
  on the VPS for non-interactive admin.

> **Status: `done`.** Phase 55 is complete — the relay candidate was benchmarked
> honestly and the WireGuard relay tunnel is up, verified, and boot-persistent.
> Non-blocking follow-up characterization (evening-peak, real-UAE-mobile path,
> GCC path) will be appended here as it's measured; it does not gate the relay
> bring-up.

</details>

- ✅ `done` — [Phase 57 — game server orchestration: operator, not raw manifests](../reference-design/13-game-networking-foundation/game-server-orchestration-operator/index.md)

### 0% — Part XIV — Backups and disaster recovery

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• RKE2 etcd snapshots
• what must be backed up
• local vs offsite
• restore tests</div></div>

- ⬜ `not-started` — [Phase 58 — RKE2 etcd snapshots](../reference-design/14-backups-and-disaster-recovery/rke2-etcd-snapshots/index.md)
- ⬜ `not-started` — [Phase 59 — what must be backed up](../reference-design/14-backups-and-disaster-recovery/what-must-be-backed-up/index.md)
- ⬜ `not-started` — [Phase 60 — local vs offsite](../reference-design/14-backups-and-disaster-recovery/local-vs-offsite/index.md)
- ⬜ `not-started` — [Phase 61 — restore tests](../reference-design/14-backups-and-disaster-recovery/restore-tests/index.md)

### 0% — Part XV — Consolidate and enforce the Ansible source of truth

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Ansible control environment
• inventory
• role ownership
• Ansible must be idempotent</div></div>

- ⬜ `not-started` — [Phase 62 — Ansible control environment](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/ansible-control-environment/index.md)
- ⬜ `not-started` — [Phase 63 — inventory](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/inventory/index.md)
- ⬜ `not-started` — [Phase 64 — role ownership](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/role-ownership/index.md)
- ⬜ `not-started` — [Phase 65 — Ansible must be idempotent](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/ansible-must-be-idempotent/index.md)

### 0% — Part XVI — Ubuntu Autoinstall

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• use Autoinstall for future clean rebuilds
• minimal safe autoinstall skeleton
• validate Autoinstall in a VM first</div></div>

- ⬜ `not-started` — [Phase 66 — use Autoinstall for future clean rebuilds](../reference-design/16-ubuntu-autoinstall/use-autoinstall-for-future-clean-rebuilds/index.md)
- ⬜ `not-started` — [Phase 67 — minimal safe autoinstall skeleton](../reference-design/16-ubuntu-autoinstall/minimal-safe-autoinstall-skeleton/index.md)
- ⬜ `not-started` — [Phase 68 — validate Autoinstall in a VM first](../reference-design/16-ubuntu-autoinstall/validate-autoinstall-in-a-vm-first/index.md)

### 100% — Part XVII — OpenTofu for external infrastructure

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:100.0%"></div></div><div class="progress-pct" style="font-size:.85em;">100%</div><div class="tip-box"><strong>Done (2)</strong>
• what OpenTofu should own
• state is sensitive
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

- ✅ `done` — [Phase 69 — what OpenTofu should own](../reference-design/17-opentofu-for-external-infrastructure/what-opentofu-should-own/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — what OpenTofu should own</summary>

# Phase 67 — what OpenTofu should own

Set up OpenTofu to own/store the *connection details* of the external
components this platform depends on (the two VPSes + the Cloudflare tunnel
credential), per Phase 67: OpenTofu is responsible for resources created
through external APIs and their connection data. Ansible remains responsible
for host configuration (apt packages, `sshd_config`, RKE2 systemd), which is
out of OpenTofu's scope.

## 67.1 What was set up

`infra/tofu/` — two OpenTofu modules, each backed by the same R2 bucket `42base`:

- `infra/tofu/vps/` — stores connection details for the two external VPSes
  (hostzealot + melbicom) via built-in `terraform_data` resources. No external
  provider exists for these VPSes, so nothing is provisioned; OpenTofu only
  tracks the *credentials* in encrypted remote state.
- `infra/tofu/cloudflare/` — stores the `cloudflared` tunnel token via
  `terraform_data`, capturing the credential that is currently a Kubernetes
  Secret.

Key files:

- `infra/tofu/vps/main.tf`, `variables.tf`, `terraform.tfvars.example`
- `infra/tofu/cloudflare/main.tf`, `variables.tf`, `terraform.tfvars.example`
- `infra/tofu/.gitignore` — ignores `*.tfstate`, `*.tfstate.*`, `.terraform/`,
  `crash.log`, `terraform.tfvars`; re-includes `!terraform.tfvars.example`.

Secret values are read from the gitignored `terraform.tfvars` (or env), never
from committed code.

## 67.2 Backend: Cloudflare R2 via the S3 backend

OpenTofu's stable release has no ORAS/GHCR backend, so Cloudflare R2 was chosen
as an S3-compatible remote state backend. Bucket `42base` holds the state keys.

Backend block (both modules, different `key`):

```hcl
terraform {
  backend "s3" {
    bucket = "42base"
    key    = "vps/terraform.tfstate"        # or "cloudflare/terraform.tfstate"
    region = "auto"
    endpoint = "https://70e06cd0a78575fb48251884ac37f859.r2.cloudflarestorage.com"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}
```

The `skip_*` options and `use_path_style = true` are required because R2 is
S3-compatible but not AWS. Credentials are supplied via the standard
`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars (region `auto`).

## 67.3 Commands run

Create the R2 bucket `42base` (via the Cloudflare API; `opentofu-state` was
created first, then deleted and replaced by `42base`):

```bash
# create bucket
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/<ACCT>/r2/buckets/42base" \
  -H "Authorization: Bearer <API_TOKEN>"

# delete the superseded bucket
curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/<ACCT>/r2/buckets/opentofu-state" \
  -H "Authorization: Bearer <API_TOKEN>"
```

Configure S3 credentials for the backend and initialize the VPS module:

```bash
export AWS_ACCESS_KEY_ID=<ACCESS_KEY_ID>
export AWS_SECRET_ACCESS_KEY=<SECRET_ACCESS_KEY>
export AWS_REGION=auto
export AWS_DEFAULT_REGION=auto

cd infra/tofu/vps
tofu init -input=false
tofu plan -input=false -no-color
tofu apply -input=false -auto-approve -no-color
```

Verify the two VPS connection records were planned and applied:

```bash
cd infra/tofu/vps
tofu plan -input=false -no-color
```

The plan shows `+ resource "terraform_data" "hostzealot"` and
`terraform_data "melbicom"` being created with their connection details
(`public_ip`, `ssh_user`, `ssh_port`, `ssh_password` — the password shows as a
sensitive value). Result: `Plan: 2 to add, 0 to change, 0 to destroy`, then
`Apply complete! Resources: 2 added`.

Repeat for the cloudflare module:

```bash
cd ../cloudflare
tofu init -input=false
tofu apply -input=false -auto-approve -no-color
```

Result: `Plan: 1 to add`, `Apply complete! Resources: 1 added`.

## 67.4 What was verified

- `tofu init` on `infra/tofu/vps` configured the R2 S3 backend successfully.
- `tofu plan` showed exactly the two VPS `terraform_data` resources.
- `tofu apply` created both, `Apply complete! Resources: 2 added`.
- `tofu apply` on `infra/tofu/cloudflare` created the tunnel-token resource,
  `Apply complete! Resources: 1 added`.
- State objects are present in R2 bucket `42base`:

```text
cloudflare/terraform.tfstate   1037 bytes
vps/terraform.tfstate          2201 bytes
```

(confirmed via an S3 `list_objects_v2` against the R2 endpoint).

## 67.5 Troubleshooting

- **403 `SignatureDoesNotMatch` during `tofu init`**: the access key ID / secret
  access key pair did not match. The bucket and endpoint were correct; the
  fault was the key pair. Fix: create a fresh R2 S3 API token in the Cloudflare
  dashboard and use its exact Access Key ID + Secret Access Key. (Also catch a
  typo in the secret — a single mistyped hex digit reproduces this error.)
- The custom domain endpoint (`s3.42base.com`) was NOT mapped to the bucket and
  returned 404 on `ListObjectsV2`; the default account endpoint
  `<ACCOUNT_ID>.r2.cloudflarestorage.com` is the correct one to use.

## 67.6 Infra encoding

- OpenTofu modules + R2 backend live in `infra/tofu/`.
- `.gitignore` protects `terraform.tfvars` (secrets) and all state files;
  `terraform.tfvars.example` is committed as documentation.
- These connection details are now reproducible + backed up in encrypted remote
  state and never need to be pasted ad hoc.

</details>

- ✅ `done` — [Phase 70 — state is sensitive](../reference-design/17-opentofu-for-external-infrastructure/state-is-sensitive/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — state is sensitive</summary>

# Phase 68 — state is sensitive

Acknowledgment note for Phase 68: OpenTofu state can contain sensitive values,
so it must never be committed. This phase's requirement is enforced by the
setup done in Phase 67.

## 68.1 What was enforced

Per Phase 68, the following are **never committed** to Git:

```text
terraform.tfstate
*.tfstate
```

Instead we use **encrypted remote state** — Cloudflare R2 (S3-compatible)
bucket `42base` — with backups. The dependency lock file is committed so
provider versions are reproducible.

This is encoded in `infra/tofu/.gitignore`:

```gitignore
# OpenTofu state is sensitive (reference-design Phase 68). Never commit.
*.tfstate
*.tfstate.*
.terraform/
# CRASH logs
crash.log
# Real secret files (gitignored)
terraform.tfvars
# But keep the example so the variable shape is documented:
!terraform.tfvars.example
```

## 68.2 Command used to verify state is not committed

Confirm the real secret files and state are ignored while the example files are
tracked:

```bash
git check-ignore -v infra/tofu/vps/terraform.tfvars        # -> ignored
git check-ignore -v infra/tofu/cloudflare/terraform.tfvars # -> ignored
git ls-files infra/tofu | grep tfvars                      # -> only *.example
```

Result: only `terraform.tfvars.example` files are committed; the real
`terraform.tfvars` and all state files stay local/remote-only.

## 68.3 What was acknowledged / used

- **Remote state:** Cloudflare R2 bucket `42base`, keys
  `vps/terraform.tfstate` and `cloudflare/terraform.tfstate`, encrypted at rest
  by R2.
- **Lockfile:** committed so provider versions are reproducible.
- **No state committed:** verified via the `git ls-files` / `git check-ignore`
  checks above.

</details>

<!-- END_GENERATED_IMPLEMENTATION -->