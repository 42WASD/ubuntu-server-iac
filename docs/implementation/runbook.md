# Build Runbook — Command Log

This is a dated, auditable record of the commands actually run on `alpha` while
implementing each build phase, together with what each command was meant to do
and what it verified.

> **How to read this:** each phase lists the commands in the order they were
> run, grouped by intent. `sudo` commands were entered by the operator directly
> into the terminal (the automation sandbox cannot type interactive passwords).

---

## Phase 0 — create the infrastructure repository first

**Intent:** establish the IaC source of truth (`infra/`) and the ownership model
before any configuration spreads across ad-hoc scripts.

Commands run:

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

---

## Phase 1 — inventory the actual machine

**Intent:** Record reality before changing anything — storage, networking,
hardware. Never guess disk names.

Commands run on `alpha`:

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

---

## Phase 2 — update Ubuntu and install base administration tools

**Intent:** Baseline OS updates, core packages, core services, and a sane
unattended-upgrades policy.

Commands run (async, sudo typed by user):

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

---

## Phase 2.1 — unattended security updates

**Intent:** confirm automatic security updates are on, reboots controlled.

Covered by the `base` role (template deployed in Phase 2). Policy:
security-updates auto, reboot only in the 03:00 maintenance window.

**Checkpoint (verified):** `systemctl --failed`, `timedatectl`, `aa-status` all
clean.

---

## Phase 3 — hostname, DNS, and local identity

**Intent:** sane hostname + `/etc/hosts`, no fake public FQDN.

Inspection (no change needed — already correct):

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

---

## Phase 4 — users, groups, and sudo boundaries

**Intent:** platform tenant groups, existing-account membership, minimal sudo —
**no new shared human account**.

### 4.1 Platform groups + `jyao`

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

### 4.2 Add the 42wasd-admin tenant user

```bash
sudo useradd -m -s /bin/bash -G ssh-users,tenant-42wasd-admin \
  -c "jyao 42admin tenant" jyao-42admin
echo 'jyao-42admin:jyao' | sudo chpasswd
```

Verified: `jyao-42admin` UID 1001, groups `jyao-42admin ssh-users
tenant-42wasd-admin`.

### 4.3 Sudo policy (minimal)

Kept `/etc/sudoers` untouched. `jyao` retains `(ALL:ALL) ALL`; no convenience
`NOPASSWD` rules for tenants.

**Checkpoint 3 (verified):**
- As a normal developer: `sudo -l` → not allowed.
- As `jyao`: `sudo -v` → works.

### Group rename (post hoc)

```bash
sudo groupmod -n tenant-42wasd-admin tenant-42admin
```
Renamed for clarity/consistency; reflected in infra + docs.

**Infra encoding:** `infra/ansible/roles/users/` — `defaults` (groups +
membership), `tasks`, `templates/platform-admin.j2`.

---

## Progress summary

| Phase | Commands run | Status |
|-------|--------------|--------|
| 0 | repo scaffold + git init | ✅ done |
| 1 | inventory (`lsblk`, `lscpu`, `lspci`, …) | ✅ done |
| 2 | apt update/full-upgrade + package install | ✅ done |
| 2.1 | unattended-upgrades policy (via base role) | ✅ done |
| 3 | hostname/hosts verify (no change) | ✅ done |
| 4 | groups + user + sudo | ✅ done |