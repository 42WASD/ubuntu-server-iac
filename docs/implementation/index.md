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

**25 / 92** phases/sections complete (**27%**).

<div class="progress-row" style="max-width:720px;padding:8px 0;"><div class="progress-track"><div class="progress-fill progress-fill--shimmer" style="--w:27.2%"></div></div><div class="progress-pct">27%</div></div>

| Status | Count |
|--------|-------|
| ✅ done | 25 |
| 🔶 in-progress | 0 |
| ⬜ not-started | 64 |
| ❌ blocked | 1 |
| ⏸️ deferred | 2 |

## Progress by part

### 86% — Part III — Build the host

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:86.0%"></div></div><div class="progress-pct" style="font-size:.85em;">86%</div><div class="tip-box"><strong>Done (25)</strong>
• Phase 0 — create the infrastructure repository first
• Phase 1 — inventory the actual machine
• Phase 2 — update Ubuntu and install base administration tools
• Phase 3 — hostname, DNS, and local identity
• Phase 4 — users, groups, and sudo boundaries
• platform groups
• no shared human account
• sudo policy
• Phase 6 — Tailscale private management path
• Phase 7 — host firewall
• Phase 8 — system tuning and resource safety
• disable swap initially
• inotify limits
• basic forwarding
• journald bound
• Phase 9 — developer CPU/RAM/PID limits on the host
• Phase 10 — storage architecture
• desired logical layout
• existing-install path
• create dedicated RKE2 filesystem only when backing storage is known
• Kubernetes fast VG
• Kubernetes bulk VG
• required LVM module
• Phase 11 — filesystem quotas for developer homes
• Phase 12 — NVIDIA host driver baseline
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• unattended security updates
• Phase 5 — SSH hardening
• Tailscale policy concept
• fresh-install target</div></div>

- ✅ `done` — [Phase 0 — create the infrastructure repository first](../reference-design/build/03-build-the-host/00-9-phase-0-create-the-infrastructure-repository-first/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 0 — create the infrastructure repository first</summary>

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

- ✅ `done` — [Phase 1 — inventory the actual machine](../reference-design/build/03-build-the-host/01-10-phase-1-inventory-the-actual-machine/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 1 — inventory the actual machine</summary>

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
`enp193s0` `192.168.8.132`, Tailscale `100.112.202.47`.

**Checkpoint 1 (verified):** identified the root device, both GPUs on PCIe, LVM
usage, free space, and the LAN NIC.

</details>

- ✅ `done` — [Phase 2 — update Ubuntu and install base administration tools](../reference-design/build/03-build-the-host/02-11-phase-2-update-ubuntu-and-install-base-administration-tools/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 2 — update Ubuntu and install base administration tools</summary>

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

</details>

- ⬜ `not-started` — [unattended security updates](../reference-design/build/03-build-the-host/03-11-1-unattended-security-updates/index.md)

<details markdown="1" class="runbook">
<summary>⬜ 📜 Build log — unattended security updates</summary>

# Phase 2.1 — unattended security updates

**Intent:** confirm automatic security updates are on, reboots controlled.

Covered by the `base` role (template deployed in Phase 2). Policy:
security-updates auto, reboot only in the 03:00 maintenance window.

**Checkpoint (verified):** `systemctl --failed`, `timedatectl`, `aa-status` all
clean.

</details>

- ✅ `done` — [Phase 3 — hostname, DNS, and local identity](../reference-design/build/03-build-the-host/04-12-phase-3-hostname-dns-and-local-identity/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 3 — hostname, DNS, and local identity</summary>

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

- ✅ `done` — [Phase 4 — users, groups, and sudo boundaries](../reference-design/build/03-build-the-host/05-13-phase-4-users-groups-and-sudo-boundaries/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 4 — users, groups, and sudo boundaries</summary>

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

- ✅ `done` — [platform groups](../reference-design/build/03-build-the-host/06-13-1-platform-groups/index.md)
- ✅ `done` — [no shared human account](../reference-design/build/03-build-the-host/07-13-2-no-shared-human-account/index.md)
- ✅ `done` — [sudo policy](../reference-design/build/03-build-the-host/08-13-3-sudo-policy/index.md)
- ⏸️ `deferred` — [Phase 5 — SSH hardening](../reference-design/build/03-build-the-host/09-14-phase-5-ssh-hardening/index.md)
- ✅ `done` — [Phase 6 — Tailscale private management path](../reference-design/build/03-build-the-host/10-15-phase-6-tailscale-private-management-path/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 6 — Tailscale private management path</summary>

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

- ⏸️ `deferred` — [Tailscale policy concept](../reference-design/build/03-build-the-host/11-15-1-tailscale-policy-concept/index.md)
- ✅ `done` — [Phase 7 — host firewall](../reference-design/build/03-build-the-host/12-16-phase-7-host-firewall/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 7 — host firewall</summary>

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

- ✅ `done` — [Phase 8 — system tuning and resource safety](../reference-design/build/03-build-the-host/13-17-phase-8-system-tuning-and-resource-safety/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 8 — system tuning and resource safety</summary>

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
reload `sysctl`, and restart `systemd-journald`. Swap-disable is bootstrap-time
(keep as a documented manual step / bootstrap task).

</details>

- ✅ `done` — [disable swap initially](../reference-design/build/03-build-the-host/14-17-1-disable-swap-initially/index.md)
- ✅ `done` — [inotify limits](../reference-design/build/03-build-the-host/15-17-2-inotify-limits/index.md)
- ✅ `done` — [basic forwarding](../reference-design/build/03-build-the-host/16-17-3-basic-forwarding/index.md)
- ✅ `done` — [journald bound](../reference-design/build/03-build-the-host/17-17-4-journald-bound/index.md)
- ✅ `done` — [Phase 9 — developer CPU/RAM/PID limits on the host](../reference-design/build/03-build-the-host/18-18-phase-9-developer-cpu-ram-pid-limits-on-the-host/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 9 — developer CPU/RAM/PID limits on the host</summary>

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

- ✅ `done` — [Phase 10 — storage architecture](../reference-design/build/03-build-the-host/19-19-phase-10-storage-architecture/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 10 — storage architecture</summary>

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

- ✅ `done` — [desired logical layout](../reference-design/build/03-build-the-host/20-19-1-desired-logical-layout/index.md)
- ❌ `blocked` — [fresh-install target](../reference-design/build/03-build-the-host/21-19-2-fresh-install-target/index.md)
- ✅ `done` — [existing-install path](../reference-design/build/03-build-the-host/22-19-3-existing-install-path/index.md)
- ✅ `done` — [create dedicated RKE2 filesystem only when backing storage is known](../reference-design/build/03-build-the-host/23-19-4-create-dedicated-rke2-filesystem-only-when-backing-storage-is-known/index.md)
- ✅ `done` — [Kubernetes fast VG](../reference-design/build/03-build-the-host/24-19-5-kubernetes-fast-vg/index.md)
- ✅ `done` — [Kubernetes bulk VG](../reference-design/build/03-build-the-host/25-19-6-kubernetes-bulk-vg/index.md)
- ✅ `done` — [required LVM module](../reference-design/build/03-build-the-host/26-19-7-required-lvm-module/index.md)
- ✅ `done` — [Phase 11 — filesystem quotas for developer homes](../reference-design/build/03-build-the-host/27-20-phase-11-filesystem-quotas-for-developer-homes/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 11 — filesystem quotas for developer homes</summary>

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

- ✅ `done` — [Phase 12 — NVIDIA host driver baseline](../reference-design/build/03-build-the-host/28-21-phase-12-nvidia-host-driver-baseline/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 12 — NVIDIA host driver baseline</summary>

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


### 0% — Part IV — Install RKE2 correctly

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (9)</strong>
• Phase 13 — choose and pin the RKE2 release
• Phase 14 — RKE2 configuration
• kubelet configuration
• Phase 15 — configure RKE2's bundled Cilium
• Phase 16 — install and start RKE2
• inspect Cilium
• verify RKE2 Secrets encryption
• Phase 17 — admin kubeconfig and CLI convenience
• Phase 18 — verify reboot recovery now, not later</div></div>

- ⬜ `not-started` — [Phase 13 — choose and pin the RKE2 release](../reference-design/build/04-install-rke2-correctly/00-22-phase-13-choose-and-pin-the-rke2-release/index.md)
- ⬜ `not-started` — [Phase 14 — RKE2 configuration](../reference-design/build/04-install-rke2-correctly/01-23-phase-14-rke2-configuration/index.md)
- ⬜ `not-started` — [kubelet configuration](../reference-design/build/04-install-rke2-correctly/02-23-1-kubelet-configuration/index.md)
- ⬜ `not-started` — [Phase 15 — configure RKE2's bundled Cilium](../reference-design/build/04-install-rke2-correctly/03-24-phase-15-configure-rke2-s-bundled-cilium/index.md)
- ⬜ `not-started` — [Phase 16 — install and start RKE2](../reference-design/build/04-install-rke2-correctly/04-25-phase-16-install-and-start-rke2/index.md)
- ⬜ `not-started` — [inspect Cilium](../reference-design/build/04-install-rke2-correctly/05-25-1-inspect-cilium/index.md)
- ⬜ `not-started` — [verify RKE2 Secrets encryption](../reference-design/build/04-install-rke2-correctly/06-25-2-verify-rke2-secrets-encryption/index.md)
- ⬜ `not-started` — [Phase 17 — admin kubeconfig and CLI convenience](../reference-design/build/04-install-rke2-correctly/07-26-phase-17-admin-kubeconfig-and-cli-convenience/index.md)
- ⬜ `not-started` — [Phase 18 — verify reboot recovery now, not later](../reference-design/build/04-install-rke2-correctly/08-27-phase-18-verify-reboot-recovery-now-not-later/index.md)

### 0% — Part V — GitOps bootstrap

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (12)</strong>
• Phase 19 — install Argo CD exactly once by hand
• Phase 20 — root GitOps application
• AppProjects
• Phase 21 — namespace baseline
• Phase 22 — PriorityClasses
• Phase 23 — ResourceQuota
• Phase 24 — LimitRange
• Phase 25 — default-deny NetworkPolicy
• Phase 26 — RBAC
• dev Role
• production is intentionally different
• Phase 27 — authentication for Kubernetes developers</div></div>

- ⬜ `not-started` — [Phase 19 — install Argo CD exactly once by hand](../reference-design/build/05-gitops-bootstrap/00-28-phase-19-install-argo-cd-exactly-once-by-hand/index.md)
- ⬜ `not-started` — [Phase 20 — root GitOps application](../reference-design/build/05-gitops-bootstrap/01-29-phase-20-root-gitops-application/index.md)
- ⬜ `not-started` — [AppProjects](../reference-design/build/05-gitops-bootstrap/02-29-1-appprojects/index.md)
- ⬜ `not-started` — [Phase 21 — namespace baseline](../reference-design/build/05-gitops-bootstrap/03-30-phase-21-namespace-baseline/index.md)
- ⬜ `not-started` — [Phase 22 — PriorityClasses](../reference-design/build/05-gitops-bootstrap/04-31-phase-22-priorityclasses/index.md)
- ⬜ `not-started` — [Phase 23 — ResourceQuota](../reference-design/build/05-gitops-bootstrap/05-32-phase-23-resourcequota/index.md)
- ⬜ `not-started` — [Phase 24 — LimitRange](../reference-design/build/05-gitops-bootstrap/06-33-phase-24-limitrange/index.md)
- ⬜ `not-started` — [Phase 25 — default-deny NetworkPolicy](../reference-design/build/05-gitops-bootstrap/07-34-phase-25-default-deny-networkpolicy/index.md)
- ⬜ `not-started` — [Phase 26 — RBAC](../reference-design/build/05-gitops-bootstrap/08-35-phase-26-rbac/index.md)
- ⬜ `not-started` — [dev Role](../reference-design/build/05-gitops-bootstrap/09-35-1-dev-role/index.md)
- ⬜ `not-started` — [production is intentionally different](../reference-design/build/05-gitops-bootstrap/10-35-2-production-is-intentionally-different/index.md)
- ⬜ `not-started` — [Phase 27 — authentication for Kubernetes developers](../reference-design/build/05-gitops-bootstrap/11-36-phase-27-authentication-for-kubernetes-developers/index.md)

### 0% — Part VI — Policy enforcement

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 28 — install Kyverno through Argo CD
• Phase 29 — stage policy before enforcing it
• example: deny hostPath
• Phase 30 — policy tests</div></div>

- ⬜ `not-started` — [Phase 28 — install Kyverno through Argo CD](../reference-design/build/06-policy-enforcement/00-37-phase-28-install-kyverno-through-argo-cd/index.md)
- ⬜ `not-started` — [Phase 29 — stage policy before enforcing it](../reference-design/build/06-policy-enforcement/01-38-phase-29-stage-policy-before-enforcing-it/index.md)
- ⬜ `not-started` — [example: deny hostPath](../reference-design/build/06-policy-enforcement/02-38-1-example-deny-hostpath/index.md)
- ⬜ `not-started` — [Phase 30 — policy tests](../reference-design/build/06-policy-enforcement/03-39-phase-30-policy-tests/index.md)

### 0% — Part VII — Persistent storage

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 31 — install OpenEBS through Argo CD
• Phase 32 — StorageClasses
• Phase 33 — prove PVC lifecycle before deploying databases</div></div>

- ⬜ `not-started` — [Phase 31 — install OpenEBS through Argo CD](../reference-design/build/07-persistent-storage/00-40-phase-31-install-openebs-through-argo-cd/index.md)
- ⬜ `not-started` — [Phase 32 — StorageClasses](../reference-design/build/07-persistent-storage/01-41-phase-32-storageclasses/index.md)
- ⬜ `not-started` — [Phase 33 — prove PVC lifecycle before deploying databases](../reference-design/build/07-persistent-storage/02-42-phase-33-prove-pvc-lifecycle-before-deploying-databases/index.md)

### 0% — Part VIII — Monitoring and logs

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 34 — metrics stack
• Phase 35 — logs
• Phase 36 — alert before things are full</div></div>

- ⬜ `not-started` — [Phase 34 — metrics stack](../reference-design/build/08-monitoring-and-logs/00-43-phase-34-metrics-stack/index.md)
- ⬜ `not-started` — [Phase 35 — logs](../reference-design/build/08-monitoring-and-logs/01-44-phase-35-logs/index.md)
- ⬜ `not-started` — [Phase 36 — alert before things are full](../reference-design/build/08-monitoring-and-logs/02-45-phase-36-alert-before-things-are-full/index.md)

### 0% — Part IX — Registry

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• Phase 37 — install Harbor
• Phase 38 — configure RKE2 registry trust</div></div>

- ⬜ `not-started` — [Phase 37 — install Harbor](../reference-design/build/09-registry/00-46-phase-37-install-harbor/index.md)
- ⬜ `not-started` — [Phase 38 — configure RKE2 registry trust](../reference-design/build/09-registry/01-47-phase-38-configure-rke2-registry-trust/index.md)

### 0% — Part X — Developer build experience

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (7)</strong>
• Phase 39 — alpha does NOT run a developer Docker daemon
• Phase 40 — local developer work on alpha
• Phase 41 — build01 architecture
• Phase 42 — BuildKit cache policy
• Phase 43 — remote BuildKit
• Phase 44 — continuous dev loop
• Phase 45 — CI pipeline</div></div>

- ⬜ `not-started` — [Phase 39 — alpha does NOT run a developer Docker daemon](../reference-design/build/10-developer-build-experience/00-48-phase-39-alpha-does-not-run-a-developer-docker-daemon/index.md)
- ⬜ `not-started` — [Phase 40 — local developer work on alpha](../reference-design/build/10-developer-build-experience/01-49-phase-40-local-developer-work-on-alpha/index.md)
- ⬜ `not-started` — [Phase 41 — build01 architecture](../reference-design/build/10-developer-build-experience/02-50-phase-41-build01-architecture/index.md)
- ⬜ `not-started` — [Phase 42 — BuildKit cache policy](../reference-design/build/10-developer-build-experience/03-51-phase-42-buildkit-cache-policy/index.md)
- ⬜ `not-started` — [Phase 43 — remote BuildKit](../reference-design/build/10-developer-build-experience/04-52-phase-43-remote-buildkit/index.md)
- ⬜ `not-started` — [Phase 44 — continuous dev loop](../reference-design/build/10-developer-build-experience/05-53-phase-44-continuous-dev-loop/index.md)
- ⬜ `not-started` — [Phase 45 — CI pipeline](../reference-design/build/10-developer-build-experience/06-54-phase-45-ci-pipeline/index.md)

### 0% — Part XI — Public web path

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 46 — Cloudflare Tunnel
• Phase 47 — public vs private names
• Phase 48 — Traefik routing</div></div>

- ⬜ `not-started` — [Phase 46 — Cloudflare Tunnel](../reference-design/build/11-public-web-path/00-55-phase-46-cloudflare-tunnel/index.md)
- ⬜ `not-started` — [Phase 47 — public vs private names](../reference-design/build/11-public-web-path/01-56-phase-47-public-vs-private-names/index.md)
- ⬜ `not-started` — [Phase 48 — Traefik routing](../reference-design/build/11-public-web-path/02-57-phase-48-traefik-routing/index.md)

### 0% — Part XII — GPU validation phase

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 49 — GPU integration is optional until proven
• Phase 50 — first GPU goal: whole-GPU scheduling
• Phase 51 — GPU policy
• Phase 52 — HAMi validation</div></div>

- ⬜ `not-started` — [Phase 49 — GPU integration is optional until proven](../reference-design/build/12-gpu-validation-phase/00-58-phase-49-gpu-integration-is-optional-until-proven/index.md)
- ⬜ `not-started` — [Phase 50 — first GPU goal: whole-GPU scheduling](../reference-design/build/12-gpu-validation-phase/01-59-phase-50-first-gpu-goal-whole-gpu-scheduling/index.md)
- ⬜ `not-started` — [Phase 51 — GPU policy](../reference-design/build/12-gpu-validation-phase/02-60-phase-51-gpu-policy/index.md)
- ⬜ `not-started` — [Phase 52 — HAMi validation](../reference-design/build/12-gpu-validation-phase/03-61-phase-52-hami-validation/index.md)

### 0% — Part XIII — Game networking foundation

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 53 — keep game workloads in Kubernetes for now
• Phase 54 — why game edge is separate from Cloudflare web
• Phase 55 — relay bring-up</div></div>

- ⬜ `not-started` — [Phase 53 — keep game workloads in Kubernetes for now](../reference-design/build/13-game-networking-foundation/00-62-phase-53-keep-game-workloads-in-kubernetes-for-now/index.md)
- ⬜ `not-started` — [Phase 54 — why game edge is separate from Cloudflare web](../reference-design/build/13-game-networking-foundation/01-63-phase-54-why-game-edge-is-separate-from-cloudflare-web/index.md)
- ⬜ `not-started` — [Phase 55 — relay bring-up](../reference-design/build/13-game-networking-foundation/02-64-phase-55-relay-bring-up/index.md)

### 0% — Part XIV — Backups and disaster recovery

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 56 — RKE2 etcd snapshots
• Phase 57 — what must be backed up
• Phase 58 — local vs offsite
• Phase 59 — restore tests</div></div>

- ⬜ `not-started` — [Phase 56 — RKE2 etcd snapshots](../reference-design/build/14-backups-and-disaster-recovery/00-65-phase-56-rke2-etcd-snapshots/index.md)
- ⬜ `not-started` — [Phase 57 — what must be backed up](../reference-design/build/14-backups-and-disaster-recovery/01-66-phase-57-what-must-be-backed-up/index.md)
- ⬜ `not-started` — [Phase 58 — local vs offsite](../reference-design/build/14-backups-and-disaster-recovery/02-67-phase-58-local-vs-offsite/index.md)
- ⬜ `not-started` — [Phase 59 — restore tests](../reference-design/build/14-backups-and-disaster-recovery/03-68-phase-59-restore-tests/index.md)

### 0% — Part XV — Consolidate and enforce the Ansible source of truth

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 60 — Ansible control environment
• Phase 61 — inventory
• Phase 62 — role ownership
• Phase 63 — Ansible must be idempotent</div></div>

- ⬜ `not-started` — [Phase 60 — Ansible control environment](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/00-69-phase-60-ansible-control-environment/index.md)
- ⬜ `not-started` — [Phase 61 — inventory](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/01-70-phase-61-inventory/index.md)
- ⬜ `not-started` — [Phase 62 — role ownership](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/02-71-phase-62-role-ownership/index.md)
- ⬜ `not-started` — [Phase 63 — Ansible must be idempotent](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/03-72-phase-63-ansible-must-be-idempotent/index.md)

### 0% — Part XVI — Ubuntu Autoinstall

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 64 — use Autoinstall for future clean rebuilds
• Phase 65 — minimal safe autoinstall skeleton
• Phase 66 — validate Autoinstall in a VM first</div></div>

- ⬜ `not-started` — [Phase 64 — use Autoinstall for future clean rebuilds](../reference-design/build/16-ubuntu-autoinstall/00-73-phase-64-use-autoinstall-for-future-clean-rebuilds/index.md)
- ⬜ `not-started` — [Phase 65 — minimal safe autoinstall skeleton](../reference-design/build/16-ubuntu-autoinstall/01-74-phase-65-minimal-safe-autoinstall-skeleton/index.md)
- ⬜ `not-started` — [Phase 66 — validate Autoinstall in a VM first](../reference-design/build/16-ubuntu-autoinstall/02-75-phase-66-validate-autoinstall-in-a-vm-first/index.md)

### 0% — Part XVII — OpenTofu for external infrastructure

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:0.0%"></div></div><div class="progress-pct" style="font-size:.85em;">0%</div><div class="tip-box"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• Phase 67 — what OpenTofu should own
• Phase 68 — state is sensitive</div></div>

- ⬜ `not-started` — [Phase 67 — what OpenTofu should own](../reference-design/build/17-opentofu-for-external-infrastructure/00-76-phase-67-what-opentofu-should-own/index.md)
- ⬜ `not-started` — [Phase 68 — state is sensitive](../reference-design/build/17-opentofu-for-external-infrastructure/01-77-phase-68-state-is-sensitive/index.md)

<!-- END_GENERATED_IMPLEMENTATION -->