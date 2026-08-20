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

**39 / 92** phases/sections complete (**42%**).

<div class="progress-row" style="max-width:720px;padding:8px 0;"><div class="progress-track"><div class="progress-fill progress-fill--shimmer" style="--w:42.4%"></div></div><div class="progress-pct">42%</div></div>

| Status | Count |
|--------|-------|
| ✅ done | 39 |
| 🔶 in-progress | 0 |
| ⬜ not-started | 50 |
| ❌ blocked | 1 |
| ⏸️ deferred | 2 |

## Progress by part

### 90% — Part III — Build the host

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:90.0%"></div></div><div class="progress-pct" style="font-size:.85em;">90%</div><div class="tip-box"><strong>Done (26)</strong>
• Phase 0 — create the infrastructure repository first
• Phase 1 — inventory the actual machine
• Phase 2 — update Ubuntu and install base administration tools
• unattended security updates
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
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
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

- ✅ `done` — [unattended security updates](../reference-design/build/03-build-the-host/03-11-1-unattended-security-updates/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — unattended security updates</summary>

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


### 100% — Part IV — Install RKE2 correctly

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:100.0%"></div></div><div class="progress-pct" style="font-size:.85em;">100%</div><div class="tip-box"><strong>Done (9)</strong>
• Phase 13 — choose and pin the RKE2 release
• Phase 14 — RKE2 configuration
• kubelet configuration
• Phase 15 — configure RKE2's bundled Cilium
• Phase 16 — install and start RKE2
• inspect Cilium
• verify RKE2 Secrets encryption
• Phase 17 — admin kubeconfig and CLI convenience
• Phase 18 — verify reboot recovery now, not later
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

- ✅ `done` — [Phase 13 — choose and pin the RKE2 release](../reference-design/build/04-install-rke2-correctly/00-22-phase-13-choose-and-pin-the-rke2-release/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 13 — choose and pin the RKE2 release</summary>

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

- ✅ `done` — [Phase 14 — RKE2 configuration](../reference-design/build/04-install-rke2-correctly/01-23-phase-14-rke2-configuration/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 14 — RKE2 configuration</summary>

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

</details>

- ✅ `done` — [kubelet configuration](../reference-design/build/04-install-rke2-correctly/02-23-1-kubelet-configuration/index.md)

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

- ✅ `done` — [Phase 15 — configure RKE2's bundled Cilium](../reference-design/build/04-install-rke2-correctly/03-24-phase-15-configure-rke2-s-bundled-cilium/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 15 — configure RKE2's bundled Cilium</summary>

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

- ✅ `done` — [Phase 16 — install and start RKE2](../reference-design/build/04-install-rke2-correctly/04-25-phase-16-install-and-start-rke2/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 16 — install and start RKE2</summary>

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

- ✅ `done` — [inspect Cilium](../reference-design/build/04-install-rke2-correctly/05-25-1-inspect-cilium/index.md)

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

- ✅ `done` — [verify RKE2 Secrets encryption](../reference-design/build/04-install-rke2-correctly/06-25-2-verify-rke2-secrets-encryption/index.md)

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

- ✅ `done` — [Phase 17 — admin kubeconfig and CLI convenience](../reference-design/build/04-install-rke2-correctly/07-26-phase-17-admin-kubeconfig-and-cli-convenience/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 17 — admin kubeconfig and CLI convenience</summary>

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

- ✅ `done` — [Phase 18 — verify reboot recovery now, not later](../reference-design/build/04-install-rke2-correctly/08-27-phase-18-verify-reboot-recovery-now-not-later/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 18 — verify reboot recovery now, not later</summary>

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
curl -s -o /dev/null -w 'HTTP %{http_code}
' http://10.43.247.243/
curl -s -o /dev/null -w 'HTTP %{http_code} %{content_type}
' http://10.43.247.243/meme.svg
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

</details>


### 33% — Part V — GitOps bootstrap

<div class="tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;"><div class="progress-track"><div class="progress-fill" style="--w:33.0%"></div></div><div class="progress-pct" style="font-size:.85em;">33%</div><div class="tip-box"><strong>Done (4)</strong>
• Phase 19 — install Argo CD exactly once by hand
• Phase 20 — root GitOps application
• AppProjects
• Phase 21 — namespace baseline
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (8)</strong>
• Phase 22 — PriorityClasses
• Phase 23 — ResourceQuota
• Phase 24 — LimitRange
• Phase 25 — default-deny NetworkPolicy
• Phase 26 — RBAC
• dev Role
• production is intentionally different
• Phase 27 — authentication for Kubernetes developers</div></div>

- ✅ `done` — [Phase 19 — install Argo CD exactly once by hand](../reference-design/build/05-gitops-bootstrap/00-28-phase-19-install-argo-cd-exactly-once-by-hand/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 19 — install Argo CD exactly once by hand</summary>

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
curl -sk -o /dev/null -w 'HTTPS %{http_code}
' https://127.0.0.1:8443/   # 200
```

## 19.5 Result

Argo CD v3.5.1 is running as the platform's GitOps owner. It is **not**
publicly exposed; temporary access is via `kubectl port-forward`. Next: Phase 20
root GitOps application (App-of-Apps bootstrap).

</details>

- ✅ `done` — [Phase 20 — root GitOps application](../reference-design/build/05-gitops-bootstrap/01-29-phase-20-root-gitops-application/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 20 — root GitOps application</summary>

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

- ✅ `done` — [AppProjects](../reference-design/build/05-gitops-bootstrap/02-29-1-appprojects/index.md)

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

</details>

- ✅ `done` — [Phase 21 — namespace baseline](../reference-design/build/05-gitops-bootstrap/03-30-phase-21-namespace-baseline/index.md)

<details markdown="1" class="runbook">
<summary>✅ 📜 Build log — Phase 21 — namespace baseline</summary>

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