# Phase 2 — update Ubuntu and install base administration tools

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
