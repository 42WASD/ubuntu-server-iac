# Ubuntu 26.04 LTS Production-Like Hosting Platform — Explained + Step-by-Step Edition

**Audit / verification date:** 2026-08-19  
**Target:** one powerful Ubuntu 26.04 LTS Server host, designed to grow into multiple machines  
**Primary node name used in examples:** `alpha`  
**Build node name used in examples:** `build01`  
**Purpose:** explain the architecture in plain English **without removing the implementation detail**, then provide a gated runbook you can follow from a clean Ubuntu install to a usable RKE2 platform.

> **Important scope note:** This is a practical infrastructure runbook for a serious single-node platform. It is deliberately conservative around destructive disk operations, host firewalls, GPU runtime changes, and cluster-wide policy. Commands containing placeholders such as `<DISK>`, `<TAILSCALE_IP>`, `<PINNED_VERSION>`, or `<DOMAIN>` are **not paste-ready until you replace and verify them**.

> **Single-node reality:** Kubernetes gives you reconciliation, scheduling, policy, declarative state, and fast recovery after a normal reboot. One physical server is still **not high availability**. A motherboard, PSU, storage-controller, or host failure can take the whole platform down.

## How to use this runbook

Treat each phase as a transaction:

```text
READ
  -> CAPTURE CURRENT STATE
      -> CHANGE ONE LAYER
          -> VALIDATE
              -> COMMIT CONFIG TO GIT
                  -> CONTINUE
```

Notation used throughout:

```text
Checkpoint
    You must prove the listed conditions before continuing.

Template
    The structure is correct, but placeholders must be replaced.

Danger / destructive
    Device names, storage, credentials, or access can be lost if copied blindly.

Optional / later
    Not required to establish the base platform.
```

### Manual commands vs Ansible

The shell commands in this document are deliberately visible so you understand what the platform is doing.

The preferred operating pattern is **not** to finish the whole machine manually and automate months later.

Use:

```text
first time you learn a phase
    -> run/verify carefully
    -> immediately encode that phase in its Ansible role
    -> rerun the role
    -> verify idempotence
    -> move to the next phase
```

So the later Ansible section is a consolidation/reference section, not permission to leave the host undocumented until the end.

---

# Part I — Understand the platform before installing anything

## 0. The one-sentence idea

Build the machine in layers and give each layer **one job**:

```text
Ubuntu Autoinstall
    -> installs/reinstalls the OS predictably

Ansible
    -> configures Linux: users, storage, SSH, Tailscale, limits, packages, RKE2

RKE2
    -> runs Kubernetes

Cilium
    -> pod networking + network policy

Traefik
    -> HTTP/HTTPS ingress into Kubernetes

Argo CD
    -> makes Kubernetes match Git

OpenEBS LocalPV LVM
    -> provisions local persistent volumes from host LVM VGs

Kyverno + Pod Security Admission
    -> prevents unsafe tenant workloads

Prometheus/Grafana/Loki/Alloy
    -> tells you what the platform is doing

Harbor
    -> stores container images

Remote BuildKit on build01
    -> performs expensive container builds away from alpha

Cloudflare
    -> public web edge / tunnel / Access

UAE relay VPS + WireGuard
    -> public game TCP/UDP path when home networking cannot expose it cleanly

OpenTofu
    -> creates external infrastructure such as Cloudflare/OCI resources
```

The critical design rule is:

```text
INSTALL != CONFIGURE != DEPLOY != BUILD != EXPOSE != BACK UP
```

Do not make one giant shell script perform all six jobs.

---

## 1. The target architecture

```text
                                  INTERNET
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 | HTTP/HTTPS                            | GAME TCP/UDP
                 v                                       v
          Cloudflare Edge                         UAE relay VPS
     DNS / CDN / WAF / Access                    public IP
                 |                                       |
         Cloudflare Tunnel                         WireGuard
                 |                                       |
                 +-------------------+-------------------+
                                     |
                                     v
+----------------------------------------------------------------------------------+
| ALPHA                                                                            |
| Ubuntu 26.04 LTS Server                                                          |
|                                                                                  |
|  Tailscale                                                                       |
|   + SSH                                                                           |
|   + private Kubernetes API                                                        |
|   + private admin endpoints                                                       |
|                                                                                  |
|  Linux developer environment                                                     |
|   + individual users                                                             |
|   + venv/npm/cargo/go/etc.                                                       |
|   + per-user cgroup limits                                                       |
|   + filesystem quotas                                                            |
|   + kubectl                                                                      |
|   + Skaffold / Buildx client                                                     |
|                       |                                                          |
|                       +----------------------- remote build -------------------+  |
|                                                                                  |
|  RKE2                                                                            |
|   + Cilium                                                                       |
|   + Traefik                                                                      |
|   + Argo CD                                                                      |
|   + OpenEBS LocalPV LVM                                                          |
|   + Kyverno                                                                      |
|   + Harbor                                                                       |
|   + Prometheus/Grafana/Loki/Alloy                                                |
|   + dev/prod/ml/gpu/game namespaces                                              |
|   + approved GPU workloads                                                       |
+----------------------------------------------------------------------------------+
                                        |
                                        | BuildKit protocol over private network
                                        v
+----------------------------------------------------------------------------------+
| BUILD01                                                                          |
| Ubuntu                                                                           |
|                                                                                  |
| LXD / KVM                                                                        |
|   + builder-jya0          -> rootless BuildKit + persistent cache                |
|   + builder-42admin       -> rootless BuildKit + persistent cache                |
|   + untrusted-ci VM       -> disposable / stronger isolation                     |
+----------------------------------------------------------------------------------+
```

---

## 2. The trust model

The platform has four different identities.

```text
HUMAN
  jyao, jya0, alice, bob, ...

PROJECT / TENANT
  tenant-jya0
  tenant-42wasd-admin

AUTOMATION
  Argo CD service accounts
  CI identities
  registry robots

MACHINE
  alpha
  build01
  future RKE2 workers
```

Do not collapse them.

Bad:

```text
five humans -> all SSH as 42admin
```

Good:

```text
alice -> Linux user alice -> member of tenant-42wasd-admin
bob   -> Linux user bob   -> member of tenant-42wasd-admin

Kubernetes group tenant-42wasd-admin
    -> dev-42wasd-admin permissions
    -> restricted prod visibility
```

Shared **project access** is useful.

Shared **human login identities** are not.

---

## 3. What each developer is allowed to do

A normal developer should be able to:

```text
SSH through Tailscale
clone Git repositories
edit source code
create Python venvs
install packages inside venvs
install project-local npm/pnpm dependencies
run unit tests
run compilers
use kubectl in authorized namespaces
view logs
exec into dev Pods
port-forward dev services
run skaffold dev
request a remote container build
push approved images to their registry project
promote their own application through GitOps
```

A normal developer should **not** be able to:

```text
sudo
become root
use cluster-admin
mount arbitrary hostPath
create privileged Pods
use hostNetwork/hostPID/hostIPC
control the host container runtime
mount /var/run/docker.sock
alter CNI / CSI / admission webhooks
change cluster-wide RBAC
request GPUs unless approved
consume unlimited CPU/RAM/disk/PIDs
read other tenants' Secrets
```

---

# 4. Five control planes, not one

The platform is easier to reason about as five control planes.

## 4.1 Linux control plane

Owned by:

```text
Ansible + jyao
```

Controls:

```text
users
groups
sudo
SSH
Tailscale
nftables
systemd
LVM/filesystems
kernel/sysctl
NVIDIA host driver
RKE2 systemd service
```

## 4.2 Kubernetes platform control plane

Owned by:

```text
Argo CD + platform-admin Git paths
```

Controls:

```text
CNI configuration
ingress
storage controller
monitoring
admission policy
registry
cluster-wide RBAC
platform namespaces
```

## 4.3 Tenant application control plane

Owned by:

```text
tenant Git repositories
```

Controls:

```text
Deployments
StatefulSets
Services
HTTPRoutes/Ingress
ConfigMaps
tenant PVCs
application-level policies
```

## 4.4 Build control plane

Owned by:

```text
build01
```

Controls:

```text
BuildKit workers
build caches
CI runners
image creation
image tests
image scanning
```

## 4.5 External edge control plane

Owned by:

```text
OpenTofu + provider APIs
```

Controls:

```text
Cloudflare DNS
Cloudflare Tunnel metadata
Cloudflare Access
relay VPS
relay firewall
public IP
```

---

# 5. Why this guide is phased

The most dangerous infrastructure mistake is installing ten moving parts before proving the first two work.

The build order is therefore:

```text
1. prove host
2. prove management access
3. prove storage
4. prove Kubernetes
5. prove cluster networking
6. prove GitOps
7. prove policy
8. prove persistent storage
9. prove application deployment
10. prove monitoring
11. prove registry/build flow
12. prove public web exposure
13. prove GPU separately
14. add game networking
15. automate reinstall/rebuild
```

Each phase has a **checkpoint**.

If a checkpoint fails, do not continue.

---

# Part II — Verified stack and current caveats

## 6. Stack selection

| Layer | Selected tool | Why |
|---|---|---|
| Host OS | Ubuntu 26.04 LTS Server | normal Linux administration, AppArmor, systemd, current LTS |
| Host automation | Ansible | idempotent Linux configuration over SSH |
| Bare-metal reinstall | Ubuntu Autoinstall | repeatable OS install |
| Kubernetes | RKE2 | production-oriented Kubernetes distribution, embedded etcd, bundled components |
| Container runtime | RKE2 embedded containerd | no host Docker daemon required |
| CNI | Cilium | eBPF networking, NetworkPolicy, observability path |
| Ingress | Traefik | native RKE2 choice for new v1.36 clusters |
| Deployment / CD | Argo CD | GitOps + strong UI + multi-team model |
| Policy | Pod Security Admission + Kyverno | baseline/restricted policy + custom organization rules |
| Local K8s storage | OpenEBS LocalPV LVM | dynamic local LVM-backed PVCs without fake single-node replication |
| Registry | Harbor | private image registry, projects, retention, scanning |
| Metrics | Prometheus + kube-state-metrics + node-exporter | platform metrics |
| UI | Grafana | metrics/log visualization |
| Logs | Loki + Grafana Alloy | centralized logs |
| Build backend | BuildKit | remote, cached image builds |
| Dev loop | Skaffold | watch/build/test/deploy/log loop |
| Build isolation | LXD containers + KVM VMs where needed | low overhead for trusted builders, stronger boundary for untrusted builds |
| Private management | Tailscale | SSH/K8s/admin reachability without public SSH |
| Public web | Cloudflare | DNS/CDN/WAF/Tunnel/Access |
| Public game edge | UAE VPS + WireGuard | generic TCP/UDP relay |
| External IaC | OpenTofu | provider-managed resources from Git |

---

## 7. Current verification caveats — read before installing

### 7.1 Ubuntu 26.04 + RKE2

Current RKE2 documentation says RKE2 should generally work on Linux distributions using systemd and iptables, while the separate SUSE support matrix defines combinations formally validated by the vendor.

This guide therefore treats Ubuntu 26.04 as:

```text
reasonable technical target
+
must pass our validation gates
+
do not assume vendor support matrix coverage merely because installation succeeds
```

### 7.2 RKE2 v1.36 ingress

The old community `ingress-nginx` Kubernetes controller reached end-of-life in March 2026.

For new RKE2 v1.36 clusters, Traefik is the default direction.

This guide explicitly selects:

```yaml
ingress-controller: traefik
```

### 7.3 GPU Operator + Ubuntu 26.04

NVIDIA's current GPU Operator platform-support matrix lists Ubuntu 22.04 and 24.04 for the validated RKE2 combinations; Ubuntu 26.04 is not currently listed in that matrix.

Therefore:

```text
DO NOT make GPU Operator a prerequisite for the base cluster.
```

First prove:

```text
Ubuntu NVIDIA driver
-> nvidia-smi
-> stable reboot
-> stable RKE2
```

Then evaluate the GPU integration separately.

### 7.4 HAMi

HAMi is an optional later layer.

Do not let:

```text
HAMi experiment fails
```

become:

```text
entire Kubernetes platform cannot boot
```

Whole-GPU scheduling comes first.

### 7.5 Local storage

OpenEBS LocalPV LVM is **local** storage.

If `alpha` dies, those volumes are unavailable until `alpha` is restored.

LocalPV provides:

```text
dynamic provisioning
filesystem/LVM management
Kubernetes PVC lifecycle
```

It does not create a second physical copy of your data on another server.

Backups are separate.

---

# 8. Version policy

Never build this platform around floating `latest`.

Use this model:

```text
Git records:
  Ubuntu release
  RKE2 minor
  exact tested RKE2 patch
  Argo CD version
  OpenEBS chart version
  Kyverno chart version
  Harbor chart version
  monitoring chart versions
```

Example variable file:

```yaml
platform_versions:
  rke2: "<PINNED_RKE2_VERSION>"
  argocd: "<PINNED_ARGOCD_VERSION>"
  openebs: "<PINNED_OPENEBS_CHART_VERSION>"
  kyverno: "<PINNED_KYVERNO_CHART_VERSION>"
  harbor: "<PINNED_HARBOR_CHART_VERSION>"
```

Rule:

```text
discover latest
    !=
automatically deploy latest
```

Instead:

```text
discover current release
-> read release notes
-> update version in Git
-> test
-> deploy
```

---

# Part III — Build the host

# 9. Phase 0 — create the infrastructure repository first

Do this from your admin workstation or from `jyao`.

Recommended repository:

```text
infra/
├── README.md
├── Makefile
├── docs/
│   ├── architecture.md
│   ├── disaster-recovery.md
│   └── upgrade-runbook.md
├── inventory/
│   ├── production.yml
│   ├── group_vars/
│   │   ├── all.yml
│   │   ├── rke2.yml
│   │   └── builders.yml
│   └── host_vars/
│       ├── alpha.yml
│       └── build01.yml
├── autoinstall/
│   ├── alpha.yaml
│   └── build01.yaml
├── ansible/
│   ├── ansible.cfg
│   ├── requirements.yml
│   ├── site.yml
│   └── roles/
│       ├── base/
│       ├── users/
│       ├── storage/
│       ├── ssh/
│       ├── tailscale/
│       ├── firewall/
│       ├── developer_limits/
│       ├── nvidia_host/
│       ├── rke2_server/
│       ├── rke2_agent/
│       ├── build_client/
│       └── build_node/
├── kubernetes/
│   ├── bootstrap/
│   │   └── argocd/
│   ├── platform/
│   │   ├── namespaces/
│   │   ├── cilium/
│   │   ├── traefik/
│   │   ├── policy/
│   │   ├── storage/
│   │   ├── monitoring/
│   │   ├── registry/
│   │   ├── cloudflare/
│   │   └── gpu/
│   └── tenants/
│       ├── jya0/
│       │   ├── dev/
│       │   ├── prod/
│       │   ├── ml/
│       │   └── gpu/
│       └── 42admin/
│           ├── dev/
│           ├── prod/
│           └── games/
├── tofu/
│   ├── cloudflare/
│   └── relay/
└── developer/
    ├── templates/
    ├── skaffold/
    └── remote-build/
```

Create it:

```bash
mkdir -p infra/{docs,inventory/{group_vars,host_vars},autoinstall,ansible/roles,kubernetes/{bootstrap/argocd,platform,tenants},tofu,developer}
cd infra
git init
```

Create a minimal Ansible entry point now:

```yaml
# ansible/site.yml

- name: Configure all Linux platform nodes
  hosts: all
  become: true
  roles:
    - base
    - users
    - tailscale
    - firewall
    - developer_limits

- name: Configure RKE2 servers
  hosts: rke2_servers
  become: true
  roles:
    - storage
    - nvidia_host
    - rke2_server

- name: Configure build nodes
  hosts: build_nodes
  become: true
  roles:
    - build_node
```

During early phases, roles that are not implemented yet can be commented out. The point is to establish the ownership model before configuration spreads across ad-hoc scripts.

Create a small `Makefile` interface:

```make
INVENTORY ?= inventory/production.yml

.PHONY: check ansible bootstrap verify

check:
	ansible-inventory -i $(INVENTORY) --graph
	ansible all -i $(INVENTORY) -m ping

ansible:
	ansible-playbook -i $(INVENTORY) ansible/site.yml

bootstrap:
	$(MAKE) check
	$(MAKE) ansible

verify:
	ansible rke2_servers -i $(INVENTORY) -a 'systemctl --failed'
```

The long-term goal is that an administrator remembers:

```bash
make check
make bootstrap
make verify
```

instead of remembering 80 one-off commands.

Create `.gitignore` immediately:

```gitignore
# secrets
*.key
*.pem
*.p12
*.pfx
.env
.env.*
!*.example

# Ansible
*.retry
.vault-password
ansible/.venv/

# OpenTofu / Terraform
**/.terraform/
**/.tofu/
*.tfstate
*.tfstate.*
*.tfplan
crash.log

# kubeconfig
kubeconfig
*.kubeconfig

# generated secrets
secrets.generated/
```

### Checkpoint 0

```bash
git status
```

Expected:

```text
clean repository after your initial commit
```

Do not continue until the repository exists.

---

# 10. Phase 1 — inventory the actual machine

Before changing storage or networking, record reality.

Run on `alpha`:

```bash
hostnamectl
uname -a
cat /etc/os-release

lscpu
free -h

lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,FSVER,MOUNTPOINTS,MODEL,SERIAL
findmnt
df -hT
df -ih

sudo pvs
sudo vgs
sudo lvs -a -o +devices

ip -br addr
ip route
resolvectl status

lspci -nn
lspci -nn | grep -i -E 'nvidia|ethernet|network|storage|nvme'

sudo smartctl --scan
sudo nvme list 2>/dev/null || true
```

Save output:

```bash
mkdir -p ~/platform-audit
{
  hostnamectl
  uname -a
  cat /etc/os-release
  lscpu
  free -h
  lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,FSVER,MOUNTPOINTS,MODEL,SERIAL
  findmnt
  df -hT
  sudo pvs
  sudo vgs
  sudo lvs -a -o +devices
  ip -br addr
  ip route
} | tee ~/platform-audit/alpha-baseline.txt
```

### Do not guess disk names

Never assume:

```text
/dev/nvme0n1 = safe disk
/dev/sda     = HDD
```

Confirm by:

```text
MODEL
SERIAL
SIZE
current mountpoints
```

A wrong `pvcreate` destroys the wrong disk just as efficiently as a correct one.

### Checkpoint 1

You should be able to answer:

```text
Which device contains /
Which physical device is the 2 TB NVMe
Which physical device is the 6 TB HDD
Whether the OS already uses LVM
How much unallocated space exists
Which NIC is the normal LAN NIC
Whether both RTX 3090s are visible on PCIe
```

Commit the **sanitized** inventory facts, not serial numbers/secrets, to:

```text
inventory/host_vars/alpha.yml
```

Example:

```yaml
host_name: alpha
os_expected: Ubuntu 26.04 LTS

hardware:
  cpu_cores: 64
  memory_gib: 128
  gpu_count: 2

storage_plan:
  nvme_class: fast
  hdd_class: bulk
```

---

# 11. Phase 2 — update Ubuntu and install base administration tools

Run:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt autoremove --purge -y
```

Install baseline packages:

```bash
sudo apt install -y \
  curl \
  wget \
  git \
  jq \
  vim \
  tmux \
  htop \
  btop \
  tree \
  unzip \
  zip \
  ca-certificates \
  gnupg \
  lsb-release \
  software-properties-common \
  acl \
  attr \
  quota \
  lvm2 \
  xfsprogs \
  smartmontools \
  nvme-cli \
  lm-sensors \
  ethtool \
  iproute2 \
  nftables \
  apparmor-utils \
  unattended-upgrades \
  needrestart \
  chrony \
  python3 \
  python3-venv \
  python3-pip
```

Enable core services:

```bash
sudo systemctl enable --now chrony
sudo systemctl enable --now smartmontools || sudo systemctl enable --now smartd

# We install nftables now, but a platform-owned service is configured later.
sudo systemctl disable nftables.service 2>/dev/null || true
```

Check time:

```bash
timedatectl
chronyc tracking
```

Check AppArmor:

```bash
sudo aa-status
```

Do **not** disable AppArmor to fix a random container problem.

Fix the actual profile/integration.

---

## 11.1 unattended security updates

Inspect:

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null || true
cat /etc/apt/apt.conf.d/50unattended-upgrades
```

Enable through Ubuntu's normal mechanism:

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

Recommended policy:

```text
automatic security updates: yes

automatic reboot:
  not blindly during work hours
```

For kernel/NVIDIA/RKE2 hosts, prefer:

```text
security package installs automatically
reboot is explicit/maintenance-window controlled
```

because a driver/kernel mismatch may require a reboot.

### Checkpoint 2

```bash
systemctl --failed
timedatectl
sudo aa-status
```

Expected:

```text
no unexplained failed units
clock synchronized
AppArmor loaded
```

---

# 12. Phase 3 — hostname, DNS, and local identity

Set hostname:

```bash
sudo hostnamectl set-hostname alpha
```

Verify:

```bash
hostnamectl
hostname -f
```

Keep `/etc/hosts` sane:

```text
127.0.0.1 localhost
127.0.1.1 alpha
```

Do not invent a fake public FQDN before the domain exists.

---

# 13. Phase 4 — users, groups, and sudo boundaries

## 13.1 platform groups

Create:

```bash
sudo groupadd -f ssh-users
sudo groupadd -f tenant-jya0
sudo groupadd -f tenant-42wasd-admin
sudo groupadd -f gpu-approved
```

Owner:

```bash
sudo usermod -aG sudo,ssh-users jyao
```

Developer:

```bash
sudo usermod -aG ssh-users,tenant-jya0 jya0
```

Future 42 contributor:

```bash
sudo adduser alice
sudo usermod -aG ssh-users,tenant-42wasd-admin alice
```

Do not add normal developers to:

```text
sudo
docker
lxd
libvirt
disk
root
```

Those groups may grant more authority than their names suggest.

---

## 13.2 no shared human account

If an account named `42admin` exists as a service/project account, prevent interactive shell access:

```bash
sudo usermod -s /usr/sbin/nologin 42admin
```

Human developers use:

```text
alice
bob
carol
```

not:

```text
everyone -> 42admin
```

---

## 13.3 sudo policy

Keep normal `/etc/sudoers` minimal.

Use:

```bash
sudo visudo -f /etc/sudoers.d/platform-admin
```

Example:

```sudoers
jyao ALL=(ALL:ALL) ALL
```

Do **not** give tenant users convenience rules such as:

```sudoers
alice ALL=(ALL) NOPASSWD: ALL
```

That negates nearly every other isolation control.

### Checkpoint 3

As a normal developer:

```bash
sudo -l
```

Expected:

```text
not allowed to run sudo
```

As `jyao`:

```bash
sudo -v
```

Expected:

```text
works
```

---

# 14. Phase 5 — SSH hardening

Create a drop-in:

```bash
sudoedit /etc/ssh/sshd_config.d/50-platform.conf
```

Recommended baseline:

```text
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes

AllowGroups ssh-users

X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding yes

ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 4
LoginGraceTime 30
```

Why keep TCP forwarding?

Because developers may legitimately use:

```text
kubectl port-forward
SSH local forwards
remote development tooling
```

Do not disable useful developer functionality unless you have a threat reason.

Validate **before restarting**:

```bash
sudo sshd -t
```

If there is no output:

```bash
sudo systemctl reload ssh
```

Keep your current SSH session open and test a second session before logging out.

### Checkpoint 4

From another machine:

```bash
ssh <user>@<current-alpha-ip>
```

Then test password authentication is rejected.

---

# 15. Phase 6 — Tailscale private management path

Install:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

Bring it up:

```bash
sudo tailscale up
```

Inspect:

```bash
tailscale status
tailscale ip -4
```

Record:

```text
alpha Tailscale IPv4 = <TAILSCALE_IP>
```

Do not put auth keys into Git.

For automated provisioning, use:

```text
short-lived / tagged / scoped auth mechanism
```

and store the secret in Ansible Vault or your CI secret store.

---

## 15.1 Tailscale policy concept

Your tailnet policy should distinguish:

```text
platform-admins
developers
build-nodes
relay-nodes
```

Conceptually:

```text
platform-admins
    -> alpha:22
    -> alpha:6443
    -> admin UIs

developers
    -> alpha:22
    -> alpha:6443
    -> only where Kubernetes RBAC allows after connection

build-nodes
    -> registry
    -> BuildKit-specific paths

random tailnet devices
    -> no implicit platform access
```

Tailscale controls **network reachability**.

Kubernetes RBAC still controls **Kubernetes authorization**.

Do not confuse them.

### Checkpoint 5

From an authorized laptop:

```bash
ping <ALPHA_TAILSCALE_IP>
ssh jyao@<ALPHA_TAILSCALE_IP>
```

Both must work before tightening public/LAN SSH access.

---

# 16. Phase 7 — host firewall

The goal is not:

```text
install nftables
-> flush everything
-> hope Kubernetes survives
```

The goal is:

```text
protect host-facing services
without taking ownership of Cilium's internal networking tables
```

Use a dedicated table.

Create a platform-owned rules file instead of taking ownership of the whole nftables ruleset:

```bash
sudo mkdir -p /etc/nftables.d
sudoedit /etc/nftables.d/host-filter.nft
```

A conservative single-node starting point:

```nft
table inet host_filter {
    chain input {
        type filter hook input priority filter; policy drop;

        ct state established,related accept
        ct state invalid drop

        iifname "lo" accept

        # ICMP / ICMPv6 are useful for MTU, reachability and IPv6 correctness.
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept

        # Tailscale management.
        iifname "tailscale0" tcp dport { 22, 6443, 9345, 10250 } accept

        # Optional: allow LAN SSH temporarily during bootstrap.
        # Replace with your real admin subnet or remove once Tailscale is proven.
        # ip saddr 192.168.1.0/24 tcp dport 22 accept
    }

    chain forward {
        type filter hook forward priority filter; policy accept;
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

Use a dedicated systemd unit which deletes **only our own table** before reloading it:

```bash
sudoedit /etc/systemd/system/platform-nftables.service
```

```ini
[Unit]
Description=Platform host nftables policy
After=network-pre.target
Before=network.target rke2-server.service
Wants=network-pre.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=-/usr/sbin/nft delete table inet host_filter
ExecStart=/usr/sbin/nft -f /etc/nftables.d/host-filter.nft
ExecReload=-/usr/sbin/nft delete table inet host_filter
ExecReload=/usr/sbin/nft -f /etc/nftables.d/host-filter.nft
ExecStop=-/usr/sbin/nft delete table inet host_filter

[Install]
WantedBy=multi-user.target
```

Validate syntax:

```bash
sudo nft -c -f /etc/nftables.d/host-filter.nft
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now platform-nftables.service
```

Inspect:

```bash
sudo nft list table inet host_filter
```

Important:

```text
Never run "nft flush ruleset" as a routine firewall reload after Kubernetes exists.
```

Our automation deletes/recreates only `inet host_filter`, leaving Cilium/Kubernetes-owned networking state alone.

### Why `forward` is not default-drop yet

Cilium/Kubernetes must move Pod traffic.

Host firewall hardening and Pod NetworkPolicy are different layers.

Do not break forwarding first and attempt to debug Cilium afterward.

### Checkpoint 6

Verify:

```text
Tailscale SSH works
Internet outbound works
DNS works
apt update works
```

Then reboot once:

```bash
sudo reboot
```

After reboot, verify again.

---

# 17. Phase 8 — system tuning and resource safety

## 17.1 disable swap initially

Check:

```bash
swapon --show
```

If swap exists, disable for the initial Kubernetes deployment:

```bash
sudo swapoff -a
```

Comment the swap entry in `/etc/fstab` if you intend to keep it disabled.

Why start this way?

```text
predictable memory accounting
fewer variables during first cluster validation
```

You can evaluate Kubernetes swap support later as a deliberate feature.

---

## 17.2 inotify limits

RKE2 documentation specifically calls out higher inotify requirements for workloads that create many watchers.

Create:

```bash
sudoedit /etc/sysctl.d/99-platform-inotify.conf
```

Use:

```sysctl
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
```

Apply:

```bash
sudo sysctl --system
```

Verify:

```bash
sysctl fs.inotify.max_user_instances
sysctl fs.inotify.max_user_watches
```

---

## 17.3 basic forwarding

Create:

```bash
sudoedit /etc/sysctl.d/99-platform-network.conf
```

Use:

```sysctl
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
```

Apply:

```bash
sudo sysctl --system
```

---

## 17.4 journald bound

Create:

```bash
sudoedit /etc/systemd/journald.conf.d/50-platform.conf
```

Example:

```ini
[Journal]
SystemMaxUse=4G
SystemKeepFree=8G
RuntimeMaxUse=1G
MaxRetentionSec=14day
Compress=yes
```

Restart:

```bash
sudo systemctl restart systemd-journald
```

Check:

```bash
journalctl --disk-usage
```

---

# 18. Phase 9 — developer CPU/RAM/PID limits on the host

Remote builds will protect alpha from Docker build spikes.

Developers can still run:

```text
pytest -n 64
make -j64
a runaway Python program
10000 child processes
```

So host users still need cgroup limits.

Systemd creates a user slice for each UID.

Find UID:

```bash
id -u jya0
id -u alice
```

For example, if Alice is UID `1005`:

```bash
sudo mkdir -p /etc/systemd/system/user-1005.slice.d
sudoedit /etc/systemd/system/user-1005.slice.d/50-platform-limits.conf
```

Example normal-developer policy:

```ini
[Slice]
CPUQuota=400%
MemoryHigh=8G
MemoryMax=12G
TasksMax=4096
IOWeight=50
```

Interpretation:

```text
CPUQuota=400%
    approximately four CPU cores worth of scheduler time

MemoryHigh=8G
    pressure/throttling boundary

MemoryMax=12G
    hard cgroup ceiling

TasksMax=4096
    process/thread ceiling

IOWeight=50
    lower I/O priority than default-weight services
```

For `jya0`, a larger profile may be appropriate:

```ini
[Slice]
CPUQuota=800%
MemoryHigh=16G
MemoryMax=24G
TasksMax=8192
IOWeight=75
```

Reload:

```bash
sudo systemctl daemon-reload
```

Existing user sessions may need to log out completely before a new slice instance picks up changes.

Check:

```bash
systemctl status user-$(id -u alice).slice
systemctl show user-$(id -u alice).slice \
  -p CPUQuotaPerSecUSec \
  -p MemoryHigh \
  -p MemoryMax \
  -p TasksMax \
  -p IOWeight
```

### Important distinction

These limits protect the **host**.

Kubernetes ResourceQuota protects a **namespace**.

BuildKit limits protect the **builder**.

Use all three at the appropriate layer.

---

# 19. Phase 10 — storage architecture

## 19.1 desired logical layout

Do not put every growing directory under `/`.

Conceptual layout:

```text
NVMe
├── EFI / boot
├── root filesystem
├── /var/log
├── /home
├── /var/lib/rancher/rke2
├── fast Kubernetes LVM VG
└── deliberately unallocated reserve

HDD
├── bulk Kubernetes LVM VG
├── model/cache area
├── local backup staging
└── deliberately unallocated reserve
```

### Why reserve free space?

Because future-you may need to extend:

```text
root
RKE2 data
home
database storage
```

LVM free extents are far more useful during an emergency than a 100%-allocated disk.

---

## 19.2 fresh-install target

For a fresh reinstall, a reasonable starting design is approximately:

```text
2 TB marketed NVMe

EFI/boot                   small
root                       ~120 GiB
/var/log                    ~64 GiB
/home                       ~96 GiB
/var/lib/rancher/rke2      ~320 GiB
Kubernetes fast VG         ~800 GiB
future VM/sandbox reserve  ~300 GiB
unallocated reserve        remaining
```

And on the 6 TB HDD:

```text
bulk Kubernetes VG         ~2.5-3.0 TiB
models/cache               ~0.5 TiB
local backup staging       ~0.7-1.0 TiB
future/game/bulk reserve   remaining
```

These are **starting allocations**, not immutable truth.

---

## 19.3 existing-install path

If Ubuntu is already installed:

**Do not repartition just to make the diagram look pretty.**

First inspect:

```bash
sudo pvs
sudo vgs
sudo lvs
lsblk -f
```

If the OS already uses LVM and has VG free space:

```text
create new LVs safely from free extents
```

If not:

```text
use the separate HDD / unused partitions
or schedule a clean reinstall later
```

Do not casually shrink a live filesystem.

---

## 19.4 create dedicated RKE2 filesystem only when backing storage is known

Example **template**, not blind command:

```bash
# DANGER: replace VG name after verifying it.
sudo lvcreate -L 320G -n rke2 <OS_VG>
sudo mkfs.xfs /dev/<OS_VG>/rke2

sudo mkdir -p /var/lib/rancher/rke2
echo '/dev/<OS_VG>/rke2 /var/lib/rancher/rke2 xfs defaults,noatime 0 2' | \
  sudo tee -a /etc/fstab

sudo mount -a
```

Validate:

```bash
findmnt /var/lib/rancher/rke2
df -hT /var/lib/rancher/rke2
```

---

## 19.5 Kubernetes fast VG

OpenEBS LocalPV LVM needs an LVM volume group.

Example desired name:

```text
vg_k8s_nvme
```

Do not manually create application LVs inside that VG.

OpenEBS owns those LVs.

Example **only after verifying the exact PV/partition**:

```bash
sudo pvcreate /dev/<NVME_K8S_PARTITION>
sudo vgcreate vg_k8s_nvme /dev/<NVME_K8S_PARTITION>
```

Check:

```bash
sudo vgs vg_k8s_nvme
```

---

## 19.6 Kubernetes bulk VG

Example:

```text
vg_k8s_hdd
```

Template:

```bash
sudo pvcreate /dev/<HDD_K8S_PARTITION>
sudo vgcreate vg_k8s_hdd /dev/<HDD_K8S_PARTITION>
```

---

## 19.7 required LVM module

OpenEBS LocalPV LVM requires LVM utilities and `dm-snapshot`.

Verify:

```bash
lsmod | grep dm_snapshot || true
```

Load:

```bash
sudo modprobe dm_snapshot
```

Persist:

```bash
echo dm_snapshot | sudo tee /etc/modules-load.d/openebs-lvm.conf
```

### Checkpoint 7

You must have:

```text
root filesystem with free headroom
/var/lib/rancher/rke2 on intended fast storage
vg_k8s_nvme visible
vg_k8s_hdd visible
at least one meaningful emergency reserve
```

Run:

```bash
df -hT
sudo pvs
sudo vgs
sudo lvs
```

Commit **the intended VG names**, not device serial secrets, to Ansible vars.

---

# 20. Phase 11 — filesystem quotas for developer homes

Cgroups limit running resources.

They do not stop:

```text
alice writes 900 GB into /home/alice
```

Use filesystem project/user quotas where your filesystem/layout supports them.

For XFS, mount options can include:

```text
uquota
pquota
```

For ext4, user/group quota support can be enabled as appropriate.

The exact command depends on how `/home` is formatted today.

The policy target:

```text
jya0:
  soft-ish operating target: 100-150 GB
  hard ceiling:             200 GB

normal developer:
  operating target:          20-30 GB
  hard ceiling:              40-50 GB
```

Shared data belongs in explicitly-managed project storage, not in one person's home directory.

### Checkpoint 8

A test developer cannot fill the entire root or home filesystem.

---

# 21. Phase 12 — NVIDIA host driver baseline

Do this **before** Kubernetes GPU integration.

List recommended server/compute drivers:

```bash
sudo ubuntu-drivers list --gpgpu
```

Let Ubuntu choose the recommended compute driver:

```bash
sudo ubuntu-drivers install --gpgpu
```

Reboot:

```bash
sudo reboot
```

Verify:

```bash
nvidia-smi
```

Expected:

```text
both RTX 3090 GPUs visible
driver loaded
no NVML mismatch
```

Also inspect:

```bash
cat /proc/driver/nvidia/version
lspci -nn | grep -i nvidia
dmesg | grep -i -E 'nvrm|nvidia' | tail -100
```

### Do not install random `.run` driver packages from NVIDIA's website

For this host, prefer Ubuntu-packaged drivers unless you have a specific compatibility reason.

### Checkpoint 9

Reboot twice.

After each reboot:

```bash
nvidia-smi
systemctl --failed
```

If GPU driver reliability is not proven, do not continue into GPU Operator/HAMi later.

The base Kubernetes platform can still continue.

---

# Part IV — Install RKE2 correctly

# 22. Phase 13 — choose and pin the RKE2 release

Use the RKE2 v1.36 line for this design.

Do not paste a floating release into production automation.

Record:

```yaml
rke2_minor: "v1.36"
rke2_version: "<EXACT_TESTED_RKE2_RELEASE>"
```

The install mechanism supports exact `INSTALL_RKE2_VERSION`.

Example shape:

```bash
curl -sfL https://get.rke2.io | \
  INSTALL_RKE2_VERSION='<EXACT_TESTED_RKE2_RELEASE>' sh -
```

Before installing, read:

```text
release notes for the selected patch
known issues
urgent Kubernetes upgrade notes
Cilium bundle version
Traefik bundle version
containerd version
```

---

# 23. Phase 14 — RKE2 configuration

Create:

```bash
sudo mkdir -p /etc/rancher/rke2
sudoedit /etc/rancher/rke2/config.yaml
```

Start with:

```yaml
node-name: alpha

cni: cilium
ingress-controller: traefik

# We will use Cilium's kube-proxy replacement.
disable-kube-proxy: true

# Keep the API certificate usable through the management address.
tls-san:
  - "<ALPHA_TAILSCALE_IP>"

# Admin kubeconfig remains root/platform-admin controlled.
write-kubeconfig-mode: "0640"

# etcd snapshots
etcd-snapshot-schedule-cron: "0 */6 * * *"
etcd-snapshot-retention: 12
etcd-snapshot-compress: true

# Basic labels for future scheduling.
node-label:
  - "platform.example.com/role=core"
  - "platform.example.com/storage-nvme=true"
  - "platform.example.com/storage-hdd=true"
  - "platform.example.com/gpu=true"
```

Do **not** put the cluster token in Git.

---

## 23.1 kubelet configuration

RKE2's current preferred pattern is to use kubelet config drop-ins rather than piling everything into CLI flags.

We want two effects:

```text
1. reserve capacity for Linux + developers + Kubernetes system services
2. protect the host from disk/memory exhaustion
```

Create the directory after RKE2 installs, or pre-create the RKE2-supported config location as part of automation.

Recommended initial target:

```text
physical:
  64 CPU
  128 GiB

leave outside normal Pod scheduling:
  roughly 12 CPU
  roughly 24 GiB

Kubernetes system reservation:
  roughly 2 CPU
  roughly 4 GiB
```

This leaves a large workload budget while admitting that SSH users and the host exist outside Pod scheduling.

Do **not** attempt to schedule 128 GiB of Pod requests on a machine where developers also compile and test software directly.

Example kubelet configuration fields to evaluate/pin in your Ansible role:

```yaml
systemReserved:
  cpu: "12"
  memory: "24Gi"
  ephemeral-storage: "20Gi"

kubeReserved:
  cpu: "2"
  memory: "4Gi"
  ephemeral-storage: "10Gi"

evictionHard:
  memory.available: "8Gi"
  nodefs.available: "12%"
  imagefs.available: "15%"
  nodefs.inodesFree: "5%"

imageGCHighThresholdPercent: 75
imageGCLowThresholdPercent: 60

seccompDefault: true
```

**Do not blindly assume the exact kubelet config schema for your pinned Kubernetes minor.** Keep this as a versioned file, validate it against the version you installed, and inspect kubelet logs after first boot.

---

# 24. Phase 15 — configure RKE2's bundled Cilium

Do not install a second upstream Cilium Helm release on top of RKE2's packaged Cilium.

Configure the packaged chart.

Create:

```bash
sudo mkdir -p /var/lib/rancher/rke2/server/manifests
sudoedit /var/lib/rancher/rke2/server/manifests/rke2-cilium-config.yaml
```

Use:

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

    hubble:
      enabled: true
      relay:
        enabled: true
      ui:
        enabled: false
```

Why disable Hubble UI initially?

Because:

```text
metrics/observability backend first
admin UI exposure later
```

Do not create another web admin surface before private access policy exists.

---

# 25. Phase 16 — install and start RKE2

Install the pinned release:

```bash
curl -sfL https://get.rke2.io | \
  INSTALL_RKE2_VERSION='<EXACT_TESTED_RKE2_RELEASE>' sh -
```

Enable:

```bash
sudo systemctl enable rke2-server
```

Start:

```bash
sudo systemctl start rke2-server
```

Follow logs:

```bash
sudo journalctl -u rke2-server -f
```

In another shell:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get nodes -o wide
```

Wait for:

```text
alpha   Ready
```

Then:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get pods -A
```

Expected critical components should settle to:

```text
Running
Completed
```

not repeated:

```text
CrashLoopBackOff
ImagePullBackOff
Pending
```

---

## 25.1 inspect Cilium

Run:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get pods -o wide | grep -i cilium
```

And:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get daemonset
```

Check no kube-proxy DaemonSet exists if kube-proxy is intentionally disabled:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get ds kube-proxy
```

Expected:

```text
NotFound
```

Check service networking:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  run dns-test \
  --rm -it \
  --restart=Never \
  --image=busybox:1.36 \
  -- nslookup kubernetes.default.svc.cluster.local
```

## 25.2 verify RKE2 Secrets encryption

RKE2 includes Secrets-at-rest encryption and the `secrets-encrypt` administration command.

Check:

```bash
sudo rke2 secrets-encrypt status
```

Expected:

```text
Encryption Status: Enabled
```

Do **not** rotate keys during initial bootstrap. Key rotation is a separate maintenance procedure and should be preceded by an etcd snapshot.

---

### Checkpoint 10 — THE BASE CLUSTER GATE

Do not continue until all are true:

```text
alpha = Ready
CoreDNS = Running
Cilium = Running
Traefik = Running
metrics-server = Running or intentionally pending while bootstrapping
DNS works inside a Pod
service networking works
no unexplained repeated restarts
```

Take a snapshot of state:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get all -A > ~/platform-audit/k8s-first-healthy.txt
```

---

# 26. Phase 17 — admin kubeconfig and CLI convenience

Do not give every developer the RKE2 admin kubeconfig.

For `jyao` only:

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/rke2/rke2.yaml ~/.kube/config
sudo chown "$USER:$USER" ~/.kube/config
chmod 600 ~/.kube/config
```

The kubeconfig's server may point at localhost.

Change it to the management IP if the admin uses it remotely:

```bash
sed -i "s/127.0.0.1/<ALPHA_TAILSCALE_IP>/" ~/.kube/config
```

Expose RKE2's bundled kubectl for admin convenience:

```bash
sudo ln -sf /var/lib/rancher/rke2/bin/kubectl /usr/local/bin/kubectl
sudo ln -sf /var/lib/rancher/rke2/bin/crictl /usr/local/bin/crictl
```

Verify:

```bash
kubectl get nodes
```

Normal developers will later get **their own identities/kubeconfigs**, not this file.

---

# 27. Phase 18 — verify reboot recovery now, not later

Before installing ten add-ons:

```bash
sudo reboot
```

After reconnecting:

```bash
systemctl is-active rke2-server
kubectl get nodes
kubectl get pods -A
```

Wait for reconciliation.

Record boot time:

```bash
systemd-analyze
systemd-analyze blame | head -30
```

### Checkpoint 11

A normal reboot should require:

```text
zero manual "docker start"
zero manual "kubectl apply"
zero manual CNI repair
```

If it does, fix that now.

---

# Part V — GitOps bootstrap

# 28. Phase 19 — install Argo CD exactly once by hand

Argo CD becomes the owner of Kubernetes configuration **after bootstrap**.

The bootstrap paradox is unavoidable:

```text
Argo cannot install itself before Argo exists
```

Do one minimal manual install.

Choose and pin an Argo CD version.

Example:

```bash
export ARGOCD_VERSION="<PINNED_ARGOCD_VERSION>"

kubectl create namespace argocd

kubectl apply \
  -n argocd \
  --server-side \
  --force-conflicts \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
```

Wait:

```bash
kubectl -n argocd rollout status deployment/argocd-server
kubectl -n argocd get pods
```

Do **not** expose Argo CD publicly yet.

Access temporarily with:

```bash
kubectl -n argocd port-forward svc/argocd-server 8443:443
```

---

# 29. Phase 20 — root GitOps application

Use a small **App-of-Apps** bootstrap rather than pointing one Application at an arbitrary directory tree.

Create:

```text
kubernetes/bootstrap/argocd/platform-root.yaml
kubernetes/bootstrap/argocd/apps/
```

Root application:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-root
  namespace: argocd
spec:
  project: default

  source:
    repoURL: "<YOUR_INFRA_GIT_REPO_URL>"
    targetRevision: main
    path: kubernetes/bootstrap/argocd/apps
    directory:
      recurse: true

  destination:
    server: https://kubernetes.default.svc
    namespace: argocd

  syncPolicy:
    automated:
      prune: true
      selfHeal: true

    syncOptions:
      - ServerSideApply=true
```

Then put child `Application` objects in `kubernetes/bootstrap/argocd/apps/`, one per platform subsystem.

Start with only namespaces:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-namespaces
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-20"
spec:
  project: default

  source:
    repoURL: "<YOUR_INFRA_GIT_REPO_URL>"
    targetRevision: main
    path: kubernetes/platform/namespaces

  destination:
    server: https://kubernetes.default.svc

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - ServerSideApply=true
```

Later add child Applications for:

```text
policy
storage
monitoring
registry
cloudflare
gpu
```

This is intentionally staged so a broken storage or GPU chart cannot prevent you from understanding whether the namespace/GitOps foundation itself works.

Apply:

```bash
kubectl apply -f kubernetes/bootstrap/argocd/platform-root.yaml
```

From here onward:

```text
if it belongs inside Kubernetes
    -> prefer Git + Argo
```

not:

```text
ssh alpha
helm install random-chart
forget what you did
```

---

## 29.1 AppProjects

Create distinct projects:

```text
platform
tenant-jya0
tenant-42wasd-admin
```

Platform project can deploy cluster-wide resources.

Tenant projects should be constrained to authorized namespaces and repositories.

This creates a second boundary in addition to Kubernetes RBAC.

---

# 30. Phase 21 — namespace baseline

Create platform namespaces:

```text
argocd
kyverno
openebs
monitoring
registry
security
ingress
build
```

Tenant namespaces:

```text
dev-jya0
prd-jya0

dev-42wasd-admin
prd-42wasd-admin

mlops

dev-games-42wasd-admin   (ephemeral staging lane)
prd-games-42wasd-admin   (canonical game lane)
```

`dev-games-42wasd-admin` is a lightweight, on-demand staging lane for deep-
copying one game server at a time (see Phase 53); it is throwaway and excluded
from canonical backups.

For tenant application namespaces, apply Pod Security labels.

Start dev namespaces with:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev-42wasd-admin
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Infrastructure namespaces may need a less restrictive policy for trusted controllers.

Do **not** label `kube-system` or CNI namespaces `restricted` without understanding their workload requirements.

---

# 31. Phase 22 — PriorityClasses

Create only a small set.

Example:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: platform-critical-custom
value: 100000
globalDefault: false
description: "Critical platform workloads managed by platform admins."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: prod-high
value: 20000
globalDefault: false
description: "Tenant production workloads."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: dev-normal
value: 1000
globalDefault: false
description: "Normal development workloads."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: build-low
value: -1000
globalDefault: false
description: "Build / disposable workloads that should yield first."
```

Avoid giant priority inflation.

If every developer can declare `platform-critical`, priorities are meaningless.

Kyverno/RBAC should restrict who may use elevated classes.

---

# 32. Phase 23 — ResourceQuota

Example `dev-42wasd-admin`:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: namespace-budget
  namespace: dev-42wasd-admin
spec:
  hard:
    requests.cpu: "4"
    limits.cpu: "8"

    requests.memory: 8Gi
    limits.memory: 16Gi

    requests.ephemeral-storage: 20Gi
    limits.ephemeral-storage: 40Gi

    requests.storage: 100Gi

    pods: "40"
    services: "15"
    persistentvolumeclaims: "10"
    configmaps: "50"
    secrets: "30"
```

Remember:

```text
quota = ceiling
quota != reservation
```

The sum of namespace ceilings may exceed node capacity.

Actual scheduling still depends on real requested resources.

---

# 33. Phase 24 — LimitRange

Example:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-defaults
  namespace: dev-42wasd-admin
spec:
  limits:
    - type: Container

      defaultRequest:
        cpu: 250m
        memory: 256Mi
        ephemeral-storage: 512Mi

      default:
        cpu: "2"
        memory: 2Gi
        ephemeral-storage: 4Gi

      max:
        cpu: "4"
        memory: 8Gi
        ephemeral-storage: 20Gi
```

This prevents the common mistake:

```yaml
resources: {}
```

from silently turning every tenant workload into an unbounded consumer.

---

# 34. Phase 25 — default-deny NetworkPolicy

Put this in every tenant namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: dev-42wasd-admin
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

Then allow DNS.

Example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-cluster-dns
  namespace: dev-42wasd-admin
spec:
  podSelector: {}
  policyTypes:
    - Egress

  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system

      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

Then add only the actual flows the application needs.

Example mental model:

```text
public frontend
    -> API
        -> PostgreSQL

random dev Pod
    -X-> PostgreSQL

compromised API
    -X-> home router / NAS / Tailscale management network
```

Cilium-specific egress controls can later enforce home-LAN exclusions more precisely.

---

# 35. Phase 26 — RBAC

## 35.1 dev Role

Example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tenant-developer
  namespace: dev-42wasd-admin
rules:
  - apiGroups: [""]
    resources:
      - pods
      - pods/log
      - pods/exec
      - pods/portforward
      - services
      - endpoints
      - configmaps
      - persistentvolumeclaims
      - events
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete

  - apiGroups: ["apps"]
    resources:
      - deployments
      - replicasets
      - statefulsets
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete

  - apiGroups: ["batch"]
    resources:
      - jobs
      - cronjobs
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete
```

Bind an identity group:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-42wasd-admin-developers
  namespace: dev-42wasd-admin
subjects:
  - kind: Group
    name: tenant-42wasd-admin
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: tenant-developer
  apiGroup: rbac.authorization.k8s.io
```

---

## 35.2 production is intentionally different

In prod, developers should mostly receive:

```text
get
list
watch
logs
events
possibly port-forward
```

Application **writes** come from Argo CD.

Why?

Because someone who can create arbitrary Pods in a namespace can often mount Secrets from that namespace even if RBAC denies direct `get secret`.

So:

```text
"cannot read Secret"
+
"can create arbitrary prod Pod"
```

is not a meaningful secret boundary.

---

# 36. Phase 27 — authentication for Kubernetes developers

Do not distribute the admin kubeconfig.

Short-term, for a small team, you can issue individual Kubernetes client credentials.

Long-term, use OIDC.

Target model:

```text
identity provider
    -> group tenant-jya0
    -> group tenant-42wasd-admin
    -> group gpu-approved
```

RKE2 API is reachable only through private management networking.

OIDC handles identity.

Kubernetes RBAC handles authorization.

This step may be postponed until the first external developer exists, but **do not solve it by copying `/etc/rancher/rke2/rke2.yaml`**.

---

# Part VI — Policy enforcement

# 37. Phase 28 — install Kyverno through Argo CD

Use a pinned Helm chart version.

Kyverno belongs in its own namespace:

```text
kyverno
```

Do not put it in `kube-system`.

Single-node note:

```text
3 replicas on one physical node
!=
real high availability
```

Start with a sensible single replica per controller, then increase only if workload volume requires it.

---

# 38. Phase 29 — stage policy before enforcing it

Do not enable 25 deny policies in one commit.

Sequence:

```text
1. install Kyverno
2. add policies in Audit
3. inspect reports
4. fix platform/tenant workloads
5. change selected policies to Enforce
```

Minimum custom controls:

```text
deny privileged containers
deny hostPath
deny hostNetwork
deny hostPID
deny hostIPC
deny hostPort unless approved
require resource requests/limits
restrict NodePort
restrict LoadBalancer
restrict storage classes
restrict high PriorityClass
restrict GPU resources
require approved registry in prod
forbid :latest in prod
prefer immutable image digests in prod
```

Pod Security `restricted` already blocks many unsafe settings.

Kyverno adds organization-specific rules and clearer exceptions.

---

## 38.1 example: deny hostPath

Concept:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-hostpath
spec:
  validationFailureAction: Audit
  background: true
  rules:
    - name: hostpath
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - "dev-*"
                - "prod-*"
                - "games-*"
      validate:
        message: "Tenant Pods may not use hostPath."
        pattern:
          spec:
            =(volumes):
              - X(hostPath): "null"
```

Treat that as a starting example; use the pinned Kyverno release's documented policy syntax and tests before Enforce.

---

# 39. Phase 30 — policy tests

Create intentionally-bad manifests under:

```text
kubernetes/policy-tests/
```

Examples:

```text
privileged-pod.yaml
hostpath-pod.yaml
hostnetwork-pod.yaml
no-resource-limits.yaml
nodeport-service.yaml
gpu-request-unapproved.yaml
```

The platform is not "secure because YAML exists."

It is secure when the forbidden test actually fails.

Example validation:

```bash
kubectl auth can-i create clusterrole --as <developer-identity>
kubectl auth can-i create pods -n dev-42wasd-admin --as <developer-identity>
kubectl auth can-i create pods -n prd-42wasd-admin --as <developer-identity>
```

Expected:

```text
cluster-wide: no
dev workload: yes
prod arbitrary write: no
```

---

# Part VII — Persistent storage

# 40. Phase 31 — install OpenEBS through Argo CD

Install OpenEBS using its pinned chart.

Because this is a single-node local-storage design:

```text
enable LocalPV LVM
do not deploy Mayastor merely to imitate replication
```

For the unified OpenEBS chart, disable the replicated Mayastor engine if you are not using it.

Keep:

```text
LocalPV LVM
```

---

# 41. Phase 32 — StorageClasses

Prefer `vgpattern` over permanently coupling manifests to a single exact VG name if you plan to add machines later.

Example fast class:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nvme-fast
provisioner: local.csi.openebs.io

allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer

parameters:
  storage: "lvm"
  vgpattern: "vg_k8s_nvme.*"
  fsType: xfs
```

Database class:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nvme-db
provisioner: local.csi.openebs.io

allowVolumeExpansion: true
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer

parameters:
  storage: "lvm"
  vgpattern: "vg_k8s_nvme.*"
  fsType: xfs
```

Bulk class:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: hdd-bulk
provisioner: local.csi.openebs.io

allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer

parameters:
  storage: "lvm"
  vgpattern: "vg_k8s_hdd.*"
  fsType: xfs
```

Start with **thick provisioning**.

Do not add:

```yaml
thinProvision: "yes"
```

until you have thin-pool monitoring and failure procedures.

---

# 42. Phase 33 — prove PVC lifecycle before deploying databases

Test:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: storage-test
  namespace: dev-jya0
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: nvme-fast
  resources:
    requests:
      storage: 2Gi
```

Mount it:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: storage-test
  namespace: dev-jya0
spec:
  containers:
    - name: test
      image: busybox:1.36
      command: ["sh", "-c", "echo hello > /data/test.txt && sleep 3600"]
      resources:
        requests:
          cpu: 10m
          memory: 16Mi
        limits:
          cpu: 100m
          memory: 64Mi
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: storage-test
```

Check:

```bash
kubectl -n dev-jya0 get pvc,pv,pod
sudo lvs
```

Delete the Pod, recreate it, confirm the data remains.

Then delete the PVC and verify the selected reclaim policy behaves exactly as intended.

### Checkpoint 12

Do not deploy PostgreSQL/Harbor until:

```text
dynamic provision works
mount works
reboot works
expansion test works
reclaim behavior is understood
```

---

# Part VIII — Monitoring and logs

# 43. Phase 34 — metrics stack

Install through Argo CD:

```text
Prometheus Operator / kube-prometheus-stack
Grafana
node-exporter
kube-state-metrics
Alertmanager
```

Start small.

Single-node default targets:

```text
Prometheus PVC: 50-100 GiB
retention:      10-15 days initially
Grafana PVC:    small
Alertmanager:   small
```

Do not allocate 500 GiB because "we have disk."

First measure ingestion.

Track:

```text
host CPU
load average
host memory
memory pressure
filesystem capacity
filesystem inode capacity
disk latency
NVMe SMART
HDD SMART
Pod CPU/RAM
restarts
OOM kills
pending Pods
PVC usage
etcd health
API latency
Cilium health
Traefik 4xx/5xx
```

---

# 44. Phase 35 — logs

Deploy:

```text
Loki
Grafana Alloy
```

Do not keep every debug log forever.

Initial policy:

```text
Kubernetes centralized logs:
  7-14 days

high-volume debug:
  shorter

security/audit logs:
  longer, preferably off-host
```

The root filesystem still gets local container/system logs.

Central logging does not remove the need for:

```text
kubelet log rotation
journald limits
application log discipline
```

---

# 45. Phase 36 — alert before things are full

Alert thresholds should include:

```text
root > 70% warning
root > 85% critical

RKE2 data filesystem > 70/85%

NVMe/HDD VG free capacity low

memory available < 16 GiB warning
memory available < 8 GiB critical

node NotReady

Cilium unavailable

API server unavailable

etcd snapshot failure

PVC approaching full

GPU temperature / utilization later

WireGuard relay loss later
```

The important alert is not:

```text
disk = 100%
```

because by then the platform is already in trouble.

---

# Part IX — Registry

# 46. Phase 37 — install Harbor

Deploy Harbor through Argo CD into:

```text
registry
```

Use dedicated persistent storage.

Do not make Harbor your only copy of source code or Dockerfiles.

Images should always be rebuildable from:

```text
Git + build pipeline
```

Harbor policy:

```text
project: jya0
project: 42admin
project: platform

production tags immutable
retention rules
vulnerability scanning
registry GC
robot accounts for CI
human access per project
```

Keep registry access:

```text
LAN/Tailscale/private first
```

Do not expose it publicly merely because Cloudflare exists.

---

# 47. Phase 38 — configure RKE2 registry trust

RKE2 uses:

```text
/etc/rancher/rke2/registries.yaml
```

for registry mirror/auth/TLS configuration.

Prefer a real TLS certificate.

Avoid an insecure HTTP registry.

After modifying registry configuration:

```bash
sudo systemctl restart rke2-server
```

Then test a harmless image pull from Harbor.

---

# Part X — Developer build experience

# 48. Phase 39 — alpha does NOT run a developer Docker daemon

On `alpha`, normal developers need:

```text
git
language tools
venv
npm/pnpm
kubectl
Skaffold
Buildx client or wrapper CLI
```

They do not need:

```text
dockerd
/var/run/docker.sock
membership in docker group
```

This is deliberate.

---

# 49. Phase 40 — local developer work on alpha

Example:

```bash
ssh jya0@alpha

cd ~/projects/my-api

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements-dev.txt
pytest
```

For Node:

```bash
corepack enable
pnpm install
pnpm test
```

OS/runtime dependencies belong in the container image.

If a project needs:

```text
ffmpeg
libpq
ImageMagick
CUDA userspace
compiler packages
```

do not give the developer sudo.

Put those in the Dockerfile/Containerfile or an approved host development package set.

---

# 50. Phase 41 — build01 architecture

Build node:

```text
build01

LXD
├── builder-jya0
├── builder-42admin
└── CI VM
```

Trusted internal builders can use unprivileged LXD system containers.

Untrusted/public PR code should use a disposable VM or hosted runner.

The builder machine owns:

```text
build CPU
build RAM
container layer extraction
image cache
build logs
temporary build files
```

Alpha does not.

---

# 51. Phase 42 — BuildKit cache policy

BuildKit supports its own garbage collection.

Example conceptual `buildkitd.toml`:

```toml
[worker.oci]
  enabled = true
  rootless = true
  max-parallelism = 8

  gc = true
  reservedSpace = "40GB"
  maxUsedSpace = "200GB"
  minFreeSpace = "100GB"
```

Then add version-appropriate GC policies for stale cache age if needed.

Meaning:

```text
keep useful cache
but never let cache consume the whole builder disk
```

Build cache belongs on build01.

Harbor retention belongs in Harbor.

Developer home quota belongs on alpha.

Three different lifecycle systems.

---

# 52. Phase 43 — remote BuildKit

The developer runs a build command from alpha.

Buildx talks to BuildKit on build01.

Conceptually:

```text
~/projects/my-api on alpha
        |
        | build context
        v
remote BuildKit
        |
        | cached build
        v
Harbor
        |
        v
dev-jya0
```

Protect the BuildKit endpoint with:

```text
private network
TLS
client certificates
tenant-specific builder
```

Do not expose unauthenticated BuildKit TCP.

---

# 53. Phase 44 — continuous dev loop

Target command:

```bash
skaffold dev
```

Desired behavior:

```text
save source
-> detect change
-> file-sync when possible
OR
-> remote build
-> run tests
-> push dev image
-> deploy dev manifest
-> tail logs
```

For interpreted languages, use file sync where practical.

Example:

```text
Python source changed
    -> sync / reload

requirements.lock changed
    -> full image rebuild
```

This keeps the loop fast while preserving a production-like container image path.

---

# 54. Phase 45 — CI pipeline

Interactive dev and CI are different.

Interactive:

```text
developer
-> skaffold dev
-> tenant builder
-> dev namespace
```

CI:

```text
Git push / PR
-> CI runner
-> lint
-> unit test
-> build
-> image scan
-> integration test
-> push immutable image
```

Production:

```text
merge/promotion
-> update GitOps image digest/tag
-> Argo CD
-> prod namespace
```

Do not give CI a permanent cluster-admin kubeconfig.

CI should mostly produce:

```text
test result
image
Git commit / promotion PR
```

Argo performs deployment.

---

# Part XI — Public web path

# 55. Phase 46 — Cloudflare Tunnel

Do this only after an internal service works.

Path:

```text
Browser
-> Cloudflare
-> cloudflared
-> Traefik
-> Service
-> Pod
```

Deploy `cloudflared` inside Kubernetes through Argo CD.

Keep its tunnel token/credential in a Kubernetes Secret managed through an encrypted secret workflow.

Important:

```text
tunnel token = credential
```

Do not commit it in plaintext.

---

# 56. Phase 47 — public vs private names

Recommended categories:

```text
PUBLIC
  status.<DOMAIN>
  docs.<DOMAIN>
  public APIs
  public project pages

CLOUDFLARE ACCESS PROTECTED
  optional web admin tools
  internal kanban
  Git web UI if desired

TAILSCALE ONLY
  Kubernetes API
  Harbor registry endpoint
  SSH
  low-level admin endpoints
  emergency tools
```

Argo/Grafana can remain Tailscale-only initially.

Do not expose every UI simply because HTTPS is available.

---

# 57. Phase 48 — Traefik routing

Prefer Gateway API/HTTPRoute where your installed RKE2 Traefik version supports your required feature cleanly.

Simple HTTP mental model:

```text
Gateway
    |
HTTPRoute host = api.jya0.<DOMAIN>
    |
Service
    |
Pods
```

Do not use NodePort as the normal public web publication mechanism.

Cloudflare Tunnel should reach the in-cluster ingress path privately.

---

# Part XII — GPU validation phase

# 58. Phase 49 — GPU integration is optional until proven

Base platform checkpoint first:

```text
RKE2 healthy
Cilium healthy
storage healthy
Argo healthy
policy healthy
monitoring healthy
```

Then GPU.

Current support caveat:

```text
Ubuntu 26.04
not currently listed in NVIDIA GPU Operator's validated Ubuntu rows
```

Therefore treat this as an engineering validation, not a guaranteed support claim.

---

# 59. Phase 50 — first GPU goal: whole-GPU scheduling

Goal:

```text
Pod asks for:
  nvidia.com/gpu: 1

scheduler sees:
  2 allocatable GPUs

Pod runs nvidia-smi/CUDA sample successfully
```

Do not install HAMi until that works.

RKE2 has GPU Operator integration guidance that accounts for its embedded containerd path.

Do **not** blindly run generic `nvidia-ctk runtime configure --runtime=containerd` against a system containerd path and assume it modified RKE2's embedded containerd.

Follow the pinned RKE2 GPU integration documentation for the RKE2 version you are actually running.

---

# 60. Phase 51 — GPU policy

Once whole-GPU scheduling works:

```text
GPU0
    production / important workloads
    whole-GPU preferred

GPU1
    experimental shared workloads
    HAMi candidate
```

Only approved namespaces may request GPU resources.

Example namespace intent:

```text
mlops
  gpu-approved=true
  gpu-tier=shared
```

Kyverno rejects GPU resources elsewhere.

---

# 61. Phase 52 — HAMi validation

Do not describe HAMi as MIG.

Test:

```text
two pods
memory cap
compute cap
concurrent CUDA
one workload intentionally exceeds memory
one workload exits/crashes
node GPU health afterward
driver reset behavior
monitoring visibility
```

The acceptance criterion is not:

```text
both Pods started
```

It is:

```text
resource limit behaves as expected
failure behavior is understood
driver remains recoverable
other tenant's workload behavior is acceptable
```

If not:

```text
fall back to whole-GPU scheduling
```

---

# Part XIII — Game networking foundation

# 62. Phase 53 — keep game workloads in Kubernetes for now

Do not solve individual game stacks yet.

Platform-level decision:

```text
prd-games-42wasd-admin
dev-games-42wasd-admin   (ephemeral staging, deep-copy on demand)
```

gets:

```text
ResourceQuota
LimitRange
NetworkPolicy
persistent storage
monitoring
controlled external ports
```

That keeps game hosting inside the same infrastructure discipline.

Later we can choose per game:

```text
plain StatefulSet
Agones
operator
proxy layer
specialized controller
```

without changing the host platform.

---

# 63. Phase 54 — why game edge is separate from Cloudflare web

Web:

```text
Cloudflare Tunnel / proxy
```

Generic game TCP/UDP:

```text
UAE VPS
-> WireGuard
-> alpha/game Service
```

Cloudflare Tunnel is not the generic free raw-UDP solution.

Keep the two traffic planes separate.

---

# 64. Phase 55 — relay bring-up

Start with one relay candidate.

Recommended experimental order:

```text
1. OCI UAE Always Free if capacity/account conditions allow
2. low-cost Dubai VPS
3. paid OCI/AWS/Azure UAE if reliability requirements justify it
```

Do not permanently choose on provider marketing.

Benchmark:

```bash
ping
mtr
iperf3
iperf3 -u
```

Measure:

```text
median latency
p95
p99
jitter
packet loss
evening peak behavior
real UAE mobile path
GCC path if relevant
```

---

# Part XIV — Backups and disaster recovery

# 65. Phase 56 — RKE2 etcd snapshots

RKE2 embedded etcd is the cluster-state database.

This guide configured:

```text
snapshot every 6 hours
retain 12 locally
compress snapshots
```

Check:

```bash
sudo rke2 etcd-snapshot list
```

Take manual snapshot before risky platform changes:

```bash
sudo rke2 etcd-snapshot save --name before-platform-change
```

Local snapshot only protects against some failures.

Copy snapshots off-host.

---

# 66. Phase 57 — what must be backed up

Back up separately:

```text
Git repositories
RKE2 etcd snapshots
RKE2 server token / recovery material
database-native backups
PVC data
Harbor config/data if not easily rebuilt
game worlds
user home directories where needed
WireGuard config
Cloudflare/OpenTofu state
Ansible Vault material
critical documentation
```

Do not store:

```text
backup
+
only copy of encryption key
```

on the same physical disk.

---

# 67. Phase 58 — local vs offsite

Three copies concept:

```text
live data
local recovery copy
offsite encrypted copy
```

The 6 TB HDD is useful for:

```text
fast local restore
staging
snapshots
```

It is not disaster recovery from:

```text
fire
theft
power event
root compromise
full-machine hardware loss
```

---

# 68. Phase 59 — restore tests

Quarterly or after major architecture changes:

```text
restore a database into a temporary namespace
restore a PVC dataset
restore an etcd snapshot in a controlled test procedure
rebuild a fresh machine from Ansible
```

A backup that has never been restored is an assumption.

---

# Part XV — Consolidate and enforce the Ansible source of truth

# 69. Phase 60 — Ansible control environment

You should already have been codifying each completed phase into Ansible. This section makes the final structure explicit and prepares the same repository to configure `build01` and future RKE2 workers.

Run Ansible from your admin laptop or a dedicated control environment.

Create venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install ansible-core
```

Create:

```yaml
# ansible/requirements.yml
collections:
  - name: ansible.posix
  - name: community.general
  - name: kubernetes.core
```

Install:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

Pin your own tested collection versions later.

---

# 70. Phase 61 — inventory

Example:

```yaml
# inventory/production.yml

all:
  children:

    rke2_servers:
      hosts:
        alpha:
          ansible_host: "<ALPHA_TAILSCALE_IP>"

    rke2_agents:
      hosts: {}

    build_nodes:
      hosts:
        build01:
          ansible_host: "<BUILD01_TAILSCALE_IP>"
```

Host vars:

```yaml
# inventory/host_vars/alpha.yml

node_role: rke2_server
rke2_node_name: alpha

developer_limits:
  jya0:
    cpu_quota_percent: 800
    memory_high: 16G
    memory_max: 24G

storage:
  k8s_fast_vg: vg_k8s_nvme
  k8s_bulk_vg: vg_k8s_hdd
```

---

# 71. Phase 62 — role ownership

`base`:

```text
packages
time
journald
AppArmor checks
sysctl
SMART
```

`users`:

```text
users
groups
SSH authorized keys
sudo
```

`tailscale`:

```text
package
service
join configuration
```

`firewall`:

```text
host_filter nftables table only
```

`developer_limits`:

```text
systemd user slice drop-ins
quota configuration
```

`storage`:

```text
mountpoints
LVM verification
safe creation only when device mappings are explicit
```

`nvidia_host`:

```text
driver installation/verification
```

`rke2_server`:

```text
RKE2 version
config.yaml
Cilium HelmChartConfig
service enable/start
health checks
```

`build_client`:

```text
Skaffold
Buildx/client wrapper
developer config
```

---

# 72. Phase 63 — Ansible must be idempotent

The test:

```bash
ansible-playbook -i inventory/production.yml ansible/site.yml
```

Run it.

Then run it again.

Second run should be mostly:

```text
changed=0
```

not:

```text
recreates users
rewrites disks
regenerates secrets
restarts RKE2 every time
```

Destructive storage operations should require an explicit opt-in variable such as:

```yaml
allow_storage_initialization: false
```

and should assert exact device serial/path information before execution.

---

# Part XVI — Ubuntu Autoinstall

# 73. Phase 64 — use Autoinstall for future clean rebuilds

Do **not** rush to reinstall the current working server merely to use Autoinstall.

First get the platform working manually + Ansible.

Then capture the known-good OS bootstrap.

Ubuntu Autoinstall can define:

```text
identity
SSH key
packages
storage layout
network
late commands
```

Use the top-level:

```yaml
#cloud-config
autoinstall:
  version: 1
```

---

# 74. Phase 65 — minimal safe autoinstall skeleton

Example:

```yaml
#cloud-config

autoinstall:
  version: 1

  locale: en_US.UTF-8
  keyboard:
    layout: us

  identity:
    hostname: alpha
    username: jyao
    password: "<CRYPTED_INSTALLER_PASSWORD>"

  ssh:
    install-server: true
    allow-pw: false
    authorized-keys:
      - "<JYAO_SSH_PUBLIC_KEY>"

  storage:
    layout:
      name: lvm

  packages:
    - curl
    - git
    - python3
    - python3-venv
    - lvm2
    - xfsprogs
    - smartmontools
    - nvme-cli
```

This is intentionally **not** the final destructive disk design.

Autoinstall storage should eventually match disks by stable identifiers such as serial/model properties.

Do not use:

```yaml
match: {}
```

on a multi-disk production machine and assume it chooses the right disk.

---

# 75. Phase 66 — validate Autoinstall in a VM first

Before using on `alpha`:

```text
create VM
attach two fake disks matching the intended size pattern
boot Ubuntu installer
feed autoinstall
verify the correct disk was destroyed
verify resulting LVM layout
verify SSH key access
```

Then use the generated installer data as another reference.

Ubuntu also writes an autoinstall representation from an installation under:

```text
/var/log/installer/autoinstall-user-data
```

Use that as a starting point, sanitize secrets, then commit your edited template.

---

# Part XVII — OpenTofu for external infrastructure

# 76. Phase 67 — what OpenTofu should own

Use OpenTofu for resources created through external APIs:

```text
Cloudflare DNS records
Cloudflare tunnel/access configuration where provider support fits
OCI relay VM
OCI VCN/security rules
AWS/Azure relay alternative
public IP resources
```

Do not use OpenTofu to manage:

```text
apt packages on alpha
/etc/ssh/sshd_config
RKE2 systemd service
```

That is Ansible's job.

---

# 77. Phase 68 — state is sensitive

OpenTofu state can contain sensitive values.

Do not commit:

```text
terraform.tfstate
*.tfstate
```

Use:

```text
encrypted remote state
or
encrypted/local protected state for early bootstrap
```

with backups.

Commit the dependency lock file when appropriate so provider versions are reproducible.

---

# Part XVIII — Day-2 operations

# 78. Upgrade order

Do not upgrade every layer in one maintenance window.

Recommended order per change set:

```text
1. backup / etcd snapshot
2. Git commit for intended version
3. host package/kernel change if required
4. reboot if required
5. RKE2 minor/patch
6. verify Cilium/Traefik
7. platform controllers
8. tenant workloads
9. GPU integration last
```

One major variable at a time.

---

# 79. RKE2 upgrade checklist

Before:

```bash
kubectl get nodes
kubectl get pods -A
sudo rke2 etcd-snapshot save --name before-rke2-upgrade
```

Read:

```text
RKE2 release notes
Kubernetes urgent upgrade notes
Cilium version change
Traefik version change
containerd version change
known issues
```

After:

```bash
kubectl get nodes
kubectl get pods -A
kubectl get events -A --sort-by=.lastTimestamp | tail -100
```

Test:

```text
DNS
HTTP ingress
PVC mount
Argo reconciliation
tenant RBAC
NetworkPolicy
GPU if enabled
```

---

# 80. Host kernel/NVIDIA update checklist

Before reboot:

```bash
uname -r
nvidia-smi
apt list --upgradable
```

After reboot:

```bash
uname -r
nvidia-smi
systemctl --failed
kubectl get nodes
kubectl get pods -A
```

Do not assume:

```text
apt upgrade succeeded
therefore GPU driver is loaded
```

---

# 81. Disk-pressure runbook

If disk approaches critical:

First identify which filesystem:

```bash
df -hT
df -ih
sudo du -xhd1 /var | sort -h
sudo du -xhd1 /var/lib/rancher/rke2 | sort -h
journalctl --disk-usage
sudo vgs
sudo lvs
```

Do not begin with:

```bash
rm -rf /var/lib/rancher/rke2/*
```

Possible safe categories:

```text
journald retention
container image GC through runtime-supported commands
old application logs
expired build cache on build01
Harbor registry GC through Harbor
old etcd snapshots beyond retention
```

Use the owner of each data type to clean it.

---

# 82. Memory-pressure runbook

Inspect:

```bash
free -h
ps aux --sort=-%mem | head -30
systemd-cgtop
kubectl top nodes
kubectl top pods -A --sort-by=memory
dmesg | grep -i -E 'oom|killed process'
```

Determine:

```text
host user process?
Kubernetes Pod?
kernel cache?
GPU-related process?
```

Do not solve every memory problem by increasing `MemoryMax`.

---

# 83. CPU-pressure runbook

Inspect:

```bash
uptime
mpstat -P ALL 1
pidstat 1
systemd-cgtop
kubectl top pods -A --sort-by=cpu
```

If host developer is responsible:

```text
user slice limit should contain it
```

If build is responsible:

```text
it should not be running on alpha
```

If Kubernetes tenant is responsible:

```text
requests/limits/quota should contain it
```

---

# 84. Network-debugging layers

Debug in this order:

```text
1. host route/DNS
2. Tailscale
3. RKE2 node health
4. Cilium
5. Kubernetes Service
6. NetworkPolicy
7. Traefik/Gateway
8. Cloudflare
```

Do not start by disabling Cilium or the firewall.

Example commands:

```bash
ip route
resolvectl status
tailscale status

kubectl get nodes
kubectl -n kube-system get pods

kubectl get svc -A
kubectl get networkpolicy -A

kubectl -n kube-system logs <cilium-pod>
kubectl -n kube-system logs <traefik-pod>
```

---

# Part XIX — Failure modes you should explicitly design for

# 85. Root filesystem fills

**Cause:**

```text
container images
logs
home directories
registry
build cache
model downloads
```

**Mitigation:**

```text
separate filesystems/VGs
user quotas
BuildKit off-host
registry storage quota
journald bound
image GC
monitoring alerts
free LVM reserve
```

---

# 86. Developer gets compromised

**Risk:**

```text
attacker has SSH as developer
```

**Expected boundary:**

```text
no sudo
no host Docker socket
cgroup limited
home quota limited
Kubernetes namespace RBAC
Pod Security restricted
Kyverno
NetworkPolicy
no other-tenant Secrets
```

If compromise immediately equals root, the platform design failed.

---

# 87. Developer has kubectl and tries privilege escalation

Protect against:

```text
privileged
hostPath
hostNetwork
hostPID
hostIPC
hostPort
dangerous RuntimeClass
unapproved NodePort
unapproved LoadBalancer
cluster-wide RBAC
```

Use:

```text
RBAC
PSA
Kyverno
restricted service account permissions
```

No single layer is sufficient.

---

# 88. CI runner is compromised

Expected:

```text
runner can build/push its authorized project
runner cannot SSH root to alpha
runner does not hold cluster-admin kubeconfig
prod deploy still comes through GitOps
```

For untrusted/public PRs:

```text
disposable VM / hosted runner
```

not a long-lived trusted builder.

---

# 89. Cilium breaks after upgrade

Mitigation:

```text
pin RKE2
read bundled Cilium release notes
snapshot etcd
change one platform layer at a time
keep console/Tailscale access to host
do not simultaneously alter nftables + Cilium + RKE2
```

---

# 90. Argo CD deletes something unexpectedly

GitOps `prune: true` is powerful.

Mitigation:

```text
platform PR review for cluster-wide paths
AppProject boundaries
separate tenant paths
Retain storage classes for critical data
backup before major refactors
review Argo diff
```

---

# 91. Admission policy locks out platform workloads

Mitigation:

```text
Audit first
policy tests
separate trusted infrastructure namespaces
explicit exceptions
version policy in Git
```

Never change:

```text
25 policies -> Enforce
```

without report review.

---

# 92. GPU integration breaks containerd/RKE2

This is why GPU is a later phase.

Mitigation:

```text
base RKE2 proven first
etcd snapshot
host driver proven
follow RKE2-specific GPU instructions
one change at a time
keep GPU workload non-critical until validated
```

---

# 93. Single server dies

Expected behavior:

```text
public web = down
Kubernetes = down
games = down
local monitoring = down
```

External status should still work.

Recovery depends on:

```text
Git
Autoinstall
Ansible
offsite etcd snapshots
offsite app data backups
documentation
```

That is why GitOps is not a substitute for backup.

---

# Part XX — Observability: how you know the platform works

# 94. Host SLO-style checks

Track:

```text
uptime
CPU saturation
load
memory pressure
swap if later enabled
root usage
RKE2 filesystem usage
inode usage
NVMe health
HDD SMART
temperatures
network errors/drops
systemd failed services
```

---

# 95. Kubernetes checks

Track:

```text
node Ready
Pod pending rate
Pod restart rate
OOM kills
API latency/errors
etcd health/snapshot age
Cilium health
CoreDNS latency/errors
Traefik error rate
PVC capacity
scheduler failures
admission denials
```

---

# 96. Tenant checks

Track per tenant:

```text
CPU request / limit usage
memory request / limit usage
PVC requested capacity
Pod count
Service count
quota percentage
restart rate
error rate
build frequency
image age
```

This lets you tune quotas from evidence instead of guessing forever.

---

# 97. Build checks

Track `build01`:

```text
BuildKit cache size
free disk
build duration
cache hit effectiveness
concurrent builds
failed builds
CPU saturation
RAM pressure
builder GC events
Harbor push failures
```

---

# 98. External-edge checks

Track:

```text
Cloudflare tunnel health
public HTTP response
relay VPS reachability
WireGuard handshake age
game TCP/UDP probe
packet loss
latency
jitter
```

---

# Part XXI — Recommended implementation sequence

# 99. Phase A — host foundation

Build exactly:

```text
Ubuntu updates
inventory
users/groups
SSH hardening
Tailscale
host firewall
systemd resource limits
storage layout
NVIDIA host driver only
```

Stop and reboot.

---

# 100. Phase B — Kubernetes foundation

Build exactly:

```text
RKE2 pinned version
Cilium
Traefik
embedded etcd snapshots
private Kubernetes API
```

Stop.

Test:

```text
node Ready
DNS
service networking
reboot
```

---

# 101. Phase C — GitOps + tenancy

Build:

```text
Argo CD
root app
namespaces
PriorityClasses
ResourceQuota
LimitRange
RBAC
PSA
NetworkPolicy
```

Stop.

Attack-test with a normal developer identity.

---

# 102. Phase D — policy + storage

Build:

```text
Kyverno Audit
policy tests
OpenEBS LocalPV LVM
nvme-fast
nvme-db
hdd-bulk
PVC lifecycle tests
```

Only then change selected Kyverno policies to Enforce.

---

# 103. Phase E — platform services

Build:

```text
Prometheus
Grafana
Loki
Alloy
Alertmanager
Harbor
```

No public exposure yet.

---

# 104. Phase F — developer workflow

Build:

```text
build01
LXD builders
BuildKit
persistent cache
BuildKit GC
Harbor auth
Buildx remote client
Skaffold dev
CI pipeline
```

Prove:

```text
developer stays SSH'd to alpha
image builds on build01
dev Pod updates
production load on alpha remains stable
```

---

# 105. Phase G — external exposure

Build:

```text
Cloudflare
cloudflared
public HTTP route
Access for selected admin web apps
external status monitoring
```

Then:

```text
relay VPS
WireGuard
game port routing
```

---

# 106. Phase H — GPU

Only now:

```text
whole-GPU Kubernetes access
monitoring
approved namespaces
GPU0/1 policy
HAMi experiment on GPU1
```

GPU failure must not block the rest of the platform.

---

# 107. Phase I — reproducibility

Once everything is proven:

```text
Ansible all manual host steps
Autoinstall clean OS
OpenTofu external infrastructure
disaster restore test
add build01
add future worker
```

That is when the architecture becomes truly reusable.

---

# Part XXII — Plain-English glossary

## RKE2

A Kubernetes distribution from Rancher/SUSE. It packages the control-plane, embedded containerd, etcd, and supported add-ons into a manageable installation.

## CNI

Container Network Interface. The integration layer Kubernetes uses for Pod networking.

## Cilium

The selected CNI. It implements networking and network policy largely using eBPF.

## Traefik

The HTTP/TCP routing controller at the Kubernetes ingress edge.

## Gateway API

A newer Kubernetes networking API model that can express gateways and routes more cleanly than the older Ingress abstraction.

## GitOps

Keeping desired infrastructure/application state in Git and continuously reconciling the live system to it.

## Argo CD

The GitOps controller selected here.

## ResourceQuota

Namespace-wide consumption ceiling.

## LimitRange

Defaults/min/max constraints for individual resources such as containers.

## Pod Security Admission

Built-in Kubernetes mechanism that applies Pod Security Standards at namespace admission time.

## Kyverno

Kubernetes-native admission policy engine for custom rules.

## LocalPV

Persistent storage whose physical data remains tied to the node/local storage rather than replicated across independent machines.

## OpenEBS LocalPV LVM

CSI provisioner that creates Kubernetes volumes from host LVM volume groups.

## Harbor

Private OCI/container image registry and project-management layer.

## BuildKit

Container image build engine.

## Buildx

Docker-compatible client front end that can send builds to BuildKit, including a remote BuildKit instance.

## Skaffold

Developer loop tool that watches code, builds/syncs, tests, deploys, and tails logs.

## LXD system container

Container with its own OS userspace that shares the host kernel.

## KVM VM

Virtual machine with a separate guest kernel and stronger isolation boundary.

## Tailscale

Private mesh networking/control layer used here for management reachability.

## Cloudflare Tunnel

Outbound connector that lets public/private web traffic reach services without exposing inbound home ports.

## WireGuard relay

A public VPS forwards game traffic through an encrypted tunnel to the home server.

## OpenTofu

Infrastructure-as-code engine for external provider resources.

## Idempotent

Running the same automation twice converges to the same intended state instead of causing repeated destructive changes.

## Reconciliation

A controller continuously comparing actual state to desired state and making corrections.

---

# Part XXIII — Compact technical reference

# 108. Host ownership matrix

| Resource | Owner |
|---|---|
| `/etc/ssh/**` | Ansible |
| `/etc/nftables.conf` | Ansible |
| `/etc/systemd/**` developer limits | Ansible |
| `/etc/rancher/rke2/config.yaml` | Ansible |
| RKE2 binary/version | Ansible |
| Cilium bootstrap HelmChartConfig | Ansible/bootstrap Git |
| Kubernetes namespaces | Argo CD |
| Kyverno policies | Argo CD |
| OpenEBS | Argo CD |
| StorageClasses | Argo CD |
| Monitoring | Argo CD |
| Harbor | Argo CD |
| Tenant applications | tenant GitOps |
| BuildKit | Ansible on build01 |
| Build cache | BuildKit GC |
| Cloudflare/relay cloud resources | OpenTofu |
| secrets | secret manager/Vault-encrypted workflow, not plaintext Git |

---

# 109. Namespace reference

```text
SYSTEM / PLATFORM
kube-system
argocd
kyverno
openebs
monitoring
registry
security
ingress
build

JYA0
dev-jya0
prd-jya0

42WASD-ADMIN
dev-42wasd-admin
prd-42wasd-admin

ML
mlops

GAMES (42wasd-admin)
dev-games-42wasd-admin   (ephemeral staging lane)
prd-games-42wasd-admin   (canonical game lane)
```

`mlops` is a single shared lane (not per-tenant `ml-jya0`/`gpu-jya0`) because
models are a shared, GPU-heavy resource consumed concurrently by any
namespace. GPU allocation inside it is governed by quota and admission, not
by namespace splitting.

---

# 110. Initial quota reference

Use these as starting ceilings, then tune from monitoring.

| Namespace | CPU request | CPU limit | RAM request | RAM limit | Ephemeral | PVC | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|
| `dev-jya0` | 4 | 8 | 8Gi | 16Gi | 40Gi | 150Gi | 0 |
| `prd-jya0` | 8 | 12 | 16Gi | 24Gi | 60Gi | 300Gi | approved |
| `mlops` | 8 | 16 | 16Gi | 32Gi | 120Gi | 500Gi | 1 shared |
| `dev-42wasd-admin` | 4 | 8 | 8Gi | 16Gi | 40Gi | 100Gi | 0 |
| `prd-42wasd-admin` | 6 | 12 | 12Gi | 24Gi | 60Gi | 200Gi | 0 |
| `prd-games-42wasd-admin` | 4 | 8 | 8Gi | 16Gi | 40Gi | 200Gi | 0 |
| `dev-games-42wasd-admin` | 2 | 4 | 4Gi | 8Gi | 20Gi | 50Gi | 0 |
| future dev | 2 | 4 | 4Gi | 8Gi | 20Gi | 50Gi | 0 |
| future prod | 4 | 8 | 8Gi | 16Gi | 40Gi | 100Gi | 0 |

Remember:

```text
sum of quotas may exceed physical capacity
```

but:

```text
sum of actual scheduled requests cannot
```

---

# 111. Host developer-limit reference

Normal developer:

```text
CPUQuota=400%
MemoryHigh=8G
MemoryMax=12G
TasksMax=4096
IOWeight=50
home hard quota ~40-50 GB
```

Heavy trusted developer (`jya0` style):

```text
CPUQuota=800%
MemoryHigh=16G
MemoryMax=24G
TasksMax=8192
IOWeight=75
home hard quota ~150-200 GB
```

Tune from measurements.

---

# 112. Network exposure reference

```text
22/tcp SSH
    Tailscale only

6443/tcp Kubernetes API
    Tailscale / RKE2 nodes only

9345/tcp RKE2 supervisor
    RKE2 nodes only

10250/tcp kubelet
    RKE2 nodes/metrics path only

public 80/443
    ideally Cloudflare path, not home-router direct exposure

game ports
    VPS relay -> WireGuard -> explicit Kubernetes/game service
```

When additional RKE2 nodes join, follow RKE2's current Cilium-specific node-to-node port requirements and restrict those ports to the node network only.

---

# 113. Storage reference

```text
ROOT / OS
  never build cache
  never model cache
  never registry bulk data

RKE2 DATA
  dedicated fast filesystem

vg_k8s_nvme
  OpenEBS owned
  fast PVCs

vg_k8s_hdd
  OpenEBS owned
  bulk PVCs

build01
  BuildKit cache

offsite
  disaster-recovery copies
```

---

# 114. Secret rules

Never commit:

```text
RKE2 token
Tailscale auth key
Cloudflare tunnel token
Cloudflare API token
Harbor admin password
registry robot secret
WireGuard private key
OpenTofu state with secrets
Ansible Vault password
private SSH key
kubeconfig with admin client certificate
```

Commit:

```text
templates
encrypted secret objects
secret names
policy
documentation
public keys when appropriate
```

---

# 115. "Bad idea" reference

Bad:

```text
shared SSH account for humans
developer sudo
developer cluster-admin
host Docker socket
privileged tenant Pods
free hostPath
no resource requests/limits
no quotas
everything on /
build cache on alpha
registry on root filesystem
plain-text secrets in Git
floating latest versions
public Kubernetes API
public Grafana/Argo without an access layer
Cloudflare Tunnel assumed to proxy all UDP games for free
3090 treated as MIG-isolated
single-node called HA
```

---

# 116. First real application acceptance test

Before calling the platform usable, deploy one small app that proves all major layers.

It should have:

```text
dev namespace
ResourceQuota
LimitRange
restricted Pod Security
NetworkPolicy
PVC
Service
Traefik route
Argo CD ownership
Harbor image
remote BuildKit build
Prometheus scrape or basic metrics
logs in Loki
Cloudflare public route
```

Developer workflow:

```text
SSH alpha
git clone
skaffold dev
change source
see dev Pod update
see logs
commit
CI test/build
promote image in Git
Argo deploys prod
```

If that loop works cleanly, your platform has proven the architecture rather than just installed software.

---

# Part XXIV — Current verification references

The following primary/current documentation was used to verify the implementation direction. Re-audit these before major upgrades because infrastructure contracts change.

1. **RKE2 Requirements**  
   https://docs.rke2.io/install/requirements  
   Confirms general Linux/systemd/iptables expectation, host/network requirements, inotify guidance, node ports, and Cilium-specific network requirements.

2. **RKE2 Quick Start**  
   https://docs.rke2.io/install/quickstart  
   Confirms installation service model, kubeconfig location, and RKE2 startup pattern.

3. **RKE2 Configuration**  
   https://docs.rke2.io/install/configuration  
   Confirms `/etc/rancher/rke2/config.yaml` and current kubelet configuration approaches.

4. **RKE2 Server Configuration Reference**  
   https://docs.rke2.io/reference/server_config  
   Confirms CNI selection, ingress-controller selection, `disable-kube-proxy`, TLS SAN, snapshot and runtime configuration fields.

5. **RKE2 Embedded Datastore**  
   https://docs.rke2.io/datastore/embedded  
   Confirms embedded etcd is RKE2's default embedded datastore and SQLite is experimental.

6. **RKE2 Backup and Restore**  
   https://docs.rke2.io/datastore/backup_restore  
   Confirms etcd snapshot management and S3-compatible off-host snapshot support.

7. **RKE2 Cilium networking options**  
   https://docs.rke2.io/networking/basic_network_options  
   Confirms bundled Cilium configuration and kube-proxy replacement integration.

8. **RKE2 Secrets Encryption**  
   https://docs.rke2.io/security/secrets_encryption  
   Confirms Secrets-at-rest encryption status/rotation tooling and the default AES-CBC provider.

9. **RKE2 GPU Operators**  
   https://docs.rke2.io/add-ons/gpu_operators  
   Confirms RKE2-specific NVIDIA GPU Operator/containerd integration details and warns that GPU Operator changes can restart RKE2.

10. **NVIDIA GPU Operator platform support**  
   https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/platform-support.html  
   Current matrix used for the Ubuntu 26.04 validation caveat.

11. **Ubuntu NVIDIA driver installation**  
    https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/  
    Confirms `ubuntu-drivers` as the recommended command-line driver installation approach and server/compute driver options.

12. **Ubuntu Autoinstall configuration reference**  
    https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html  
    Confirms YAML structure, storage layouts, LVM behavior, disk matching, SSH identity, and action-based storage configuration.

13. **Ubuntu Autoinstall provisioning guide**  
    https://canonical-subiquity.readthedocs-hosted.com/en/latest/tutorial/providing-autoinstall.html  
    Confirms cloud-init / media delivery modes.

14. **Argo CD Getting Started**  
    https://argo-cd.readthedocs.io/en/latest/getting_started/  
    Confirms official install flow and recommends pinning a concrete Argo CD version for production.

15. **Argo CD Installation**  
    https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/  
    Confirms multi-tenant deployment model.

16. **OpenEBS Installation**  
    https://openebs.io/docs/main/quickstart-guide/installation  
    Confirms current unified install direction and LocalPV configuration considerations.

17. **OpenEBS LocalPV LVM StorageClass**  
    https://openebs.io/docs/user-guides/local-storage-user-guide/local-pv-lvm/configuration/lvm-create-storageclass  
    Confirms LocalPV LVM provisioner, `vgpattern`/`volgroup`, filesystems, scheduling, and expansion options.

18. **OpenEBS LocalPV prerequisites**  
    https://openebs.io/docs/main/quickstart-guide/prerequisites  
    Confirms LVM utilities / kernel module / VG prerequisites.

19. **Kyverno Installation**  
    https://kyverno.io/docs/installation/installation/  
    Confirms Helm is the recommended production installation method and Kyverno belongs in a dedicated namespace.

20. **Kubernetes Pod Security Admission**  
    https://kubernetes.io/docs/concepts/security/pod-security-admission/  
    Confirms namespace-level `privileged`, `baseline`, and `restricted` Pod Security enforcement.

21. **Kubernetes ResourceQuota**  
    https://kubernetes.io/docs/concepts/policy/resource-quotas/  
    Confirms namespace aggregate resource enforcement.

22. **Kubernetes LimitRange**  
    https://kubernetes.io/docs/concepts/policy/limit-range/  
    Confirms default/min/max resource constraints at namespace admission.

23. **Docker Buildx remote driver**  
    https://docs.docker.com/build/builders/drivers/remote/  
    Confirms Buildx can connect to externally managed BuildKit and supports TLS client configuration.

24. **BuildKit cache garbage collection**  
    https://docs.docker.com/build/cache/garbage-collection/  
    Confirms automatic cache GC and age/size policy model.

25. **Skaffold dev loop**  
    https://skaffold.dev/docs/workflows/dev/  
    Confirms source watching, file sync/build/test/deploy/log development workflow.

26. **Tailscale Linux install**  
    https://tailscale.com/kb/1031/install-linux  
    Confirms Linux installation and `tailscale up` path.

27. **Cloudflare Tunnel**  
    https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/  
    Confirms outbound tunnel architecture for published/private applications.

28. **OpenTofu providers/state**  
    https://opentofu.org/docs/language/providers/  
    https://opentofu.org/docs/language/state/  
    Confirms provider dependency/configuration model and state handling.

---


# Part XXV — Final build order

For this exact platform, do it in this order:

```text
01  Git infrastructure repository
02  host inventory / disk verification
03  Ubuntu update + base packages
04  users/groups/sudo
05  SSH hardening
06  Tailscale
07  host nftables
08  sysctl/journald
09  developer cgroup + disk quotas
10  storage/LVM
11  NVIDIA host driver only
12  pinned RKE2
13  bundled Cilium config
14  Traefik
15  reboot validation
16  Argo CD bootstrap
17  namespaces/RBAC/quota/LimitRange
18  Pod Security + NetworkPolicy
19  Kyverno audit
20  OpenEBS LocalPV LVM
21  PVC tests
22  monitoring/logging
23  Harbor
24  build01 + remote BuildKit
25  Skaffold developer loop
26  CI pipeline
27  Cloudflare
28  external status
29  UAE WireGuard relay
30  game platform
31  whole-GPU Kubernetes test
32  GPU policy
33  HAMi experiment
34  offsite backups
35  Ansible conversion
36  Autoinstall validation
37  OpenTofu external resources
38  full disaster-recovery test
39  add future RKE2 workers
```

The rule throughout is:

```text
PROVE
    -> AUTOMATE
        -> VERSION
            -> MONITOR
                -> BACK UP
                    -> ONLY THEN EXPAND
```

That is the difference between a pile of installed software and a platform you can trust, reproduce, and grow.
