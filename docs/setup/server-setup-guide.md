# Server Setup Guide

This guide documents the complete setup of the Ubuntu server (`alpha`) — from VPN connectivity to system monitoring and GPU driver installation.

**Host:** `alpha` · **User:** `jyao` · **Environment:** Ubuntu Server 26.04 (headless, CLI only)

## Table of Contents

1. [GlobalProtect VPN Setup](#globalprotect-vpn-setup)
2. [DNS Fix for systemd-resolved](#dns-fix-for-systemd-resolved)
3. [HIP (Host Health) Script](#hip-host-health-script)
4. [System Hardening and Access](#system-hardening-and-access)
5. [Internal AI VS Code SSL Configuration](#internal-ai-vs-code-ssl-configuration)
6. [SSH Connection Keep-Alive](#ssh-connection-keep-alive)
7. [Hardware Monitoring](#hardware-monitoring)
8. [NVIDIA GPU Driver](#nvidia-gpu-driver)
9. [Key Files](#key-files)
10. [Verification Checklist](#verification-checklist)
11. [Troubleshooting](#troubleshooting)

---

## GlobalProtect VPN Setup

The server connects to the **ecouncil.ae** corporate VPN (`vpn.ecouncil.ae`) using the **GlobalProtect** protocol with **SAML** authentication. This requires a two-script approach:

- `connect-vpn.sh` — performs SAML auth and opens the VPN tunnel.
- `vpn-dns-wrapper.sh` — fixes DNS for `systemd-resolved` once the tunnel is up.

### The Problem

1. **SAML auth is interactive** — GlobalProtect requires a browser login (SSO) returning a `preloginCookie`.
2. **`openconnect`'s default script does not push DNS to `systemd-resolved`** on this distro, so internal hostnames fail to resolve.
3. The gateway expects a **HIP report** (host integrity check).

### Final solution: `gpauth` + `openconnect`

The working combination uses the **`globalprotect-openconnect`** PPA, which provides:

- `gpauth` → performs SAML auth and emits JSON containing the `preloginCookie`.
- `openconnect` → establishes the GlobalProtect tunnel using that cookie.

**Current approach in `connect-vpn.sh`:**

1. `gpauth --browser remote --gateway vpn.ecouncil.ae` → returns `AUTH_JSON`.
2. Extract `preloginCookie` and `username` from the JSON.
3. Pipe the cookie into `sudo openconnect --protocol=gp --usergroup=gateway:prelogin-cookie --os=win --passwd-on-stdin`.
4. Use `--script=$DNS_WRAPPER` (DNS fix) and `--csd-wrapper=$HIP_SCRIPT` (HIP compliance).

### Running the VPN in the Background

While `tmux` works, **`systemd` is better** for VPN connections:

| Criterion | systemd | tmux |
|-----------|---------|------|
| Auto-restart | Reconnects automatically | No reconnect |
| Security | Runs as a dedicated service | Needs active terminal |
| Logging | `journalctl -u ...` | Manual scroll |
| Lifecycle | Clean disconnect/cleanup | Manual cleanup |

For daily manual use, the recommended approach is a **detached tmux session that auto-restarts**:

```bash
tmux new-session -d -s vpn "while true; do cd ~ && ./connect-vpn.sh; echo '[!] VPN exited, restarting in 10s...'; sleep 10; done"
tmux attach -t vpn
```

---

## DNS Fix for systemd-resolved

Created `vpn-dns-wrapper.sh`, used as the `--script` argument for `openconnect`. On `connect`/`reconnect` it:

- Calls the original `/usr/share/vpnc-scripts/vpnc-script` to set up routes and the TUN interface.
- Clears stale settings (`resolvectl revert`).
- Pushes VPN-internal DNS servers (`INTERNAL_IP4_DNS`).
- Adds VPN domains as both **search domains** and **routing domains** (`~` prefix) for split-DNS.
- On `disconnect`, reverts DNS.

Verified with `resolvectl query litellm.adeoaiengine.ecouncil.ae`.

---

## HIP (Host Health) Script

The gateway requires a HIP report. `connect-vpn.sh` looks for `hipreport.sh` under `/usr /etc /opt` and `~/.config/openconnect`; if absent, it downloads the official script from the openconnect GitLab repo into `~/.config/openconnect/hipreport.sh`.

---

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

See the [full SSH Connection Guide](../guides/ssh-connection-guide.md) for details.

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

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/vpn/connect-vpn.sh` | Main VPN launcher |
| `scripts/vpn/vpn-dns-wrapper.sh` | openconnect `--script`: DNS fix |
| `scripts/vpn/vpn-persist.sh` | VPN persistence loop |
| `~/.config/openconnect/hipreport.sh` | HIP host-report script |
| `~/.bashrc`, `~/.profile` | `NODE_TLS_REJECT_UNAUTHORIZED=0` |

---

## Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| VPN Connected | `ip addr show tun0` | Assigned IP |
| Internal DNS | `resolvectl query litellm...` | Internal IP |
| CPU Temp | `sensors` | Tctl shown |
| GPU Driver | `nvidia-smi` | 2 × RTX 3090, driver 595.71.05 |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Failed to obtain prelogin cookie` | SAML auth failed | Re-run `gpauth`; check SSO session |
| Hostnames not resolving | DNS not applied | Check `resolvectl status tun0` |
| VPN drops | firewall/UFW | Allow OpenSSH, re-enable UFW |
| Internal TLS errors | self-signed certs | `NODE_TLS_REJECT_UNAUTHORIZED=0` |