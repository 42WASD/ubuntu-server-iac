# Server Setup Guide

This guide documents the base setup and administration of the Ubuntu server (`alpha`): system hardening, access control, monitoring, and driver installation.

**Host:** `alpha` · **User:** `jyao` · **Environment:** Ubuntu Server 26.04 (headless, CLI only)

## Table of Contents

1. [System Hardening and Access](#system-hardening-and-access)
2. [Internal AI VS Code SSL Configuration](#internal-ai-vs-code-ssl-configuration)
3. [SSH Connection Keep-Alive](#ssh-connection-keep-alive)
4. [Hardware Monitoring](#hardware-monitoring)
5. [NVIDIA GPU Driver](#nvidia-gpu-driver)
6. [Kubernetes (MicroK8s) Removal](#kubernetes-microk8s-removal)
7. [Key Files](#key-files)
8. [Verification Checklist](#verification-checklist)
9. [Troubleshooting](#troubleshooting)

!!! note
    VPN connectivity is covered in the dedicated [VPN Connection Guide](../guides/connectivity/vpn-guide.md).

## System Hardening and Access

- **UFW**: disabled during testing, re-enabled later; `OpenSSH` allowed.
- **SSH server**: `openssh-server` installed and enabled (`systemctl enable --now ssh`).
- **Tailscale**: installed, `tailscaled` enabled, `tailscale up` started.
- **TLS for Node/VS Code**: `NODE_TLS_REJECT_UNAUTHORIZED=0` set in `~/.bashrc`, `~/.profile`, `~/.zshrc`.
- **`resolvconf`**: installed for DNS troubleshooting.

---

## Internal AI VS Code SSL Configuration

Internal AI endpoints (e.g. `litellm.stanford...`) use **self-signed certificates**. Both **Local macOS** and **Remote Linux** environments must be configured.

### Local macOS
```bash
launchctl setenv NODE_TLS_REJECT_UNAUTHORIZED 0
```
*(Restart VS Code with `Cmd + Q` after.)*

### VS Code Remote Settings
`~/.vscode-server/data/Machine/settings.json`:
```json
{
    "http.proxyStrictSSL": false,
    "http.systemCertificates": true
}
```

### Inject env vars on remote host
```bash
echo 'export NODE_TLS_REJECT_UNAUTHORIZED=0' >> ~/.bashrc
echo 'export NODE_TLS_REJECT_UNAUTHORIZED=0' >> ~/.profile
```

---

## SSH Connection Keep-Alive

To prevent SSH drops during inactivity, the following rule was added to the **local macOS** client config at `~/.ssh/config`:

```ssh_config
Host *
  ServerAliveInterval 30
  ServerAliveCountMax 3
  TCPKeepAlive yes
```

| Setting | Value | Purpose |
|---------|-------|---------|
| `ServerAliveInterval` | `30` | Keep-alive ping every 30s when idle |
| `ServerAliveCountMax` | `3` | Drop after 3 unacknowledged pings |
| `TCPKeepAlive` | `yes` | TCP-level keepalive |

See the [full SSH Connection Guide](../guides/connectivity/ssh-connection-guide.md) for details.

---

## Hardware Monitoring

Installed `lm-sensors` and `btop`:

```bash
sudo apt install -y lm-sensors btop
sudo sensors-detect --auto
```

Quick temperature check:
```bash
sensors
```

Live dashboard:
```bash
btop
```

Current monitoring results (idle):
- CPU (EPYC 7742): `Tctl` ~44°C, CCDs 39-45°C
- NVMe SSD: ~38°C

---

## NVIDIA GPU Driver

The server has **2 × NVIDIA RTX 3090** (GA102, Ampere). The **proprietary server driver** was installed:

```bash
sudo apt install -y nvidia-driver-595-server nvidia-utils-595-server
```

- Version: **595.71.05**
- Secure Boot: **disabled** (clean DKMS build, no MOK signing prompt)
- **A reboot is required** after install to load the kernel module.

Verify after reboot:
```bash
nvidia-smi
```

Both GPUs are **power-limited to 300W** via a systemd service to reduce heat and power draw. See the dedicated [GPU Power Limiting guide](../guides/hardware/gpu-power-limit-guide.md) for details.

---

## Kubernetes (MicroK8s) Removal

A **MicroK8s** cluster (Canonical's lightweight Kubernetes distribution) was previously installed via snap. It was running `kubelite` (the unified daemon running the kubelet, kube-apiserver, scheduler, controller-manager and kube-proxy) plus its control-plane services. As it was no longer needed and consumed CPU/memory, it was **completely removed including all data**:

```bash
sudo snap remove --purge microk8s
```

Verification that it is fully gone:

```bash
snap list | grep -i microk8s       # nothing
systemctl list-units | grep -i microk8s   # nothing
ps aux | grep -iE 'kubelite|k8s-dqlite'   # nothing
```

This freed **1.8 GB** of snap data and stopped the associated processes (`kubelite`, `k8s-dqlite`, `calico-node`, `containerd`).

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/gpu/gpu-power-limit.service` | systemd GPU 300W power limit service |
| `~/.config/openconnect/hipreport.sh` | HIP host-report script |
| `~/.bashrc`, `~/.profile` | `NODE_TLS_REJECT_UNAUTHORIZED=0` |

---

## Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| SSH | `ssh alpha` | Connects |
| CPU Temp | `sensors` | Tctl shown |
| GPU Driver | `nvidia-smi` | 2 × RTX 3090, driver 595.71.05 |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| SSH drops after idle | NAT/firewall idle timeout | See [SSH Connection guide](../guides/connectivity/ssh-connection-guide.md) |
| Internal TLS errors | self-signed certs | `NODE_TLS_REJECT_UNAUTHORIZED=0` |