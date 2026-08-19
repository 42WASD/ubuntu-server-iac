# Work Guide: GlobalProtect VPN Setup & System Configuration

**User:** `jyao` (jyao@ECOUNCIL.AE)
**Host:** `alpha`
**Date range:** 2026-08-17 → 2026-08-19
**Environment:** Linux (Ubuntu Server 26.04) + Remote VS Code

---

## Table of Contents

1. [Project Summary](#project-summary)
2. [The Problem](#the-problem)
3. [What Was Done](#what-was-done)
4. [Running the VPN in the Background](#running-the-vpn-in-the-background-systemd-vs-tmux)
5. [Internal AI / VS Code SSL Configuration](#internal-ai-vs-code-ssl-configuration)
6. [Key Files](#key-files)
7. [How to Use](#how-to-use)
8. [Verification Checklist](#verification-checklist)
9. [Troubleshooting](#troubleshooting)
10. [Security Notes](#security-notes)

---

## Project Summary

The goal was to connect this Linux machine to the **ecouncil.ae corporate VPN** (`vpn.ecouncil.ae`) using the **GlobalProtect** protocol. The corporate gateway uses **SAML (Okta-style) authentication**, which is interactive (browser-based). This was solved with a two-script approach:

- `connect-vpn.sh` — performs SAML auth and opens the VPN tunnel.
- `vpn-dns-wrapper.sh` — fixes DNS for `systemd-resolved` once the tunnel is up.

Several other one-time system tasks were also completed (SSH server, Tailscale, TLS config), described below.

---

## The Problem

1. **SAML auth is interactive** — GlobalProtect gateways here require a browser login (SSO) and return a `preloginCookie` that must be passed to `openconnect`.
2. **`openconnect`'s default `vpnc-script` does not push DNS to `systemd-resolved`** properly on this distro, so internal hostnames (e.g. `litellm.adeoaiengine.ecouncil.ae`) fail to resolve.
3. The gateway also expects a **HIP report** (host integrity check), so a `hipreport.sh` script is required via `--csd-wrapper`.

---

## What Was Done

### Phase 1 — Tried several VPN clients (learning/cleanup)

The history shows a series of attempts before settling on the final approach:

- **`openconnect-sso`** (pip/`uv`) — attempted with `uv venv`, Python 3.10, Playwright; repeatedly failed due to a stale dependency constraint, then was cleaned up.
- **`globalprotect-openconnect`** + `gpclient`/`gpauth` — attempted via PPA `ppa:yuezk/globalprotect-openconnect`. `gpauth` successfully returns SAML JSON; piping it into `gpclient connect --cookie-on-stdin` was tried.
- **`gp-saml-gui`** (pipx) — tried, removed.
- **Package cleanup** — removed Playwright browser binaries, `uv`/`pip` caches, pipx data, dev libs (`libxml2-dev`, `libxslt1-dev`, etc.), and uninstalled test packages to keep the system clean.

### Phase 2 — Final solution: `gpauth` + `openconnect`

The working combination uses the **`globalprotect-openconnect`** PPA, which provides:

- `gpauth` → performs SAML auth and emits JSON containing the `preloginCookie`.
- `openconnect` → establishes the GlobalProtect tunnel using that cookie.
- `gpclient` → higher-level wrapper.

**Current approach** in `connect-vpn.sh`:

1. `gpauth --browser remote --gateway vpn.ecouncil.ae` → returns `AUTH_JSON`.
2. Extract `preloginCookie` and `username` from the JSON.
3. Pipe the cookie into `sudo openconnect --protocol=gp --usergroup=gateway:prelogin-cookie --os=win --passwd-on-stdin`.
4. Use `--script=$DNS_WRAPPER` (DNS fix) and `--csd-wrapper=$HIP_SCRIPT` (HIP compliance).

### Phase 3 — DNS fix for `systemd-resolved`

Created `vpn-dns-wrapper.sh`, used as the `--script` argument for `openconnect`. On `connect`/`reconnect` it:

- Calls the original `/usr/share/vpnc-scripts/vpnc-script` to set up routes and the TUN interface.
- Clears stale settings for the interface (`resolvectl revert`).
- Pushes VPN-internal DNS servers (`INTERNAL_IP4_DNS`).
- Adds VPN domains (from `CISCO_DEF_DOMAIN`, `CISCO_SPLIT_DNS`, `CISCO_SPLIT_INC_*`) as both **search domains** and **routing domains** (`~` prefix) for split-DNS.
- On `disconnect`, reverts DNS to avoid stale entries.

Verified with `resolvectl query litellm.adeoaiengine.ecouncil.ae` → successful.

### Phase 4 — HIP (host health) script

- The gateway requires a HIP report.
- `connect-vpn.sh` looks for `hipreport.sh` under `/usr /etc /opt` and `~/.config/openconnect`.
- If absent, it downloads the official script from the openconnect GitLab repo into `~/.config/openconnect/hipreport.sh`.

### Phase 5 — System hardening / access setup (one-time)

- **UFW**: disabled (`sudo ufw disable`) during testing, re-enabled later; allowed `OpenSSH`.
- **SSH server**: installed `openssh-server`, enabled via `systemctl enable --now ssh`, verified listening on port 22 (`ss -tulpn`).
- **Tailscale**: installed via the official script, enabled `tailscaled`, and started `tailscale up`.
- **TLS for Node/VS Code**: set `NODE_TLS_REJECT_UNAUTHORIZED=0` in `~/.bashrc`, `~/.profile`, and `~/.zshrc` to bypass self-signed cert validation for internal tools.
- **`resolvconf`**: installed (`sudo apt install resolvconf`) as part of DNS troubleshooting.

---

## Running the VPN in the Background (Systemd vs Tmux)

While `tmux` works, **`systemd` is significantly better** for VPN connections on Ubuntu Server.

### Why `systemd` is better than `tmux` for VPNs

| Criterion | `systemd` | `tmux` |
|-----------|-----------|--------|
| **Auto-restart** | Reconnects automatically if the VPN drops or the server reboots. | Leaves a dead session; no reconnect. |
| **Security** | Runs as a dedicated service — no active user login or exposed terminal needed. | Requires a terminal/SSH session to stay open. |
| **Logging** | Built-in journaling via `journalctl -u ...`. | Manual scroll through tmux output. |
| **Lifecycle** | Properly runs disconnect scripts and cleans up DNS/routes on stop. | Requires manual cleanup. |

### Step 3 — Create a Systemd Service

Create the service file:

```bash
sudo nano /etc/systemd/system/globalprotect-vpn.service
```

Paste the following (replace `jyao` with your actual username):

```ini
[Unit]
Description=GlobalProtect OpenConnect VPN
After=network-online.target systemd-resolved.service
Wants=network-online.target

[Service]
Type=simple
User=jyao
Group=jyao
ExecStartPre=/usr/bin/gpauth --browser remote --gateway vpn.ecouncil.ae --output /tmp/gp-auth.json
ExecStart=/bin/bash -c 'COOKIE=$(cat /tmp/gp-auth.json | grep -o "\"preloginCookie\":\"[^\"]*" | cut -d"\"" -f4); USER=$(cat /tmp/gp-auth.json | grep -o "\"username\":\"[^\"]*" | cut -d"\"" -f4); echo "$COOKIE" | /usr/sbin/openconnect --protocol=gp -u "$USER" --usergroup=gateway:prelogin-cookie --os=win --script=/home/jyao/vpn-dns-wrapper.sh --csd-wrapper=/home/jyao/.config/openconnect/hipreport.sh --passwd-on-stdin vpn.ecouncil.ae'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> ⚠️ **Important Note on SAML + Systemd:** Because `gpauth` requires **interactive browser authentication**, fully automating this via systemd requires either storing the cookie temporarily (as shown above) or using a token-based auth method if your company supports it. For daily manual use, simply running `./connect-vpn.sh` inside `tmux` is perfectly fine (see the recommendation at the end of this guide).

Enable and start the service (if using the systemd approach):

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now globalprotect-vpn.service
```

Check status/logs:

```bash
sudo systemctl status globalprotect-vpn.service
journalctl -u globalprotect-vpn.service -f
```

---

## Internal AI / VS Code SSL Configuration

Your internal AI endpoints (e.g. `litellm.adeoaiengine.ecouncil.ae`) use **self-signed certificates**. VS Code runs in two environments — **Local macOS** and **Remote Linux** — and both must be configured.

### Step 1 — Configure Local macOS Settings

VS Code launched from the Dock does **not** read shell profiles. Inject the variable directly into the macOS GUI environment:

```bash
launchctl setenv NODE_TLS_REJECT_UNAUTHORIZED 0
```

*(Restart VS Code completely with `Cmd + Q` after running this.)*

### Step 2 — Configure VS Code Remote Settings (Machine Profile)

When connected via SSH, VS Code uses a separate settings file for extensions running on the remote host.

1. Connect to the remote server via SSH.
2. Open Command Palette: `Ctrl + Shift + P`.
3. Select **Preferences: Open Remote Settings (JSON)**.
   *(Ensure the tab says **Remote**; path should be `~/.vscode-server/data/Machine/settings.json`).*
4. Add these lines:

```json
{
    "http.proxyStrictSSL": false,
    "http.systemCertificates": true
}
```

5. Save (`Ctrl + S`).

### Step 3 — Inject Environment Variables into Remote Linux Host

The OAI extension spawns Node.js child processes that **ignore `proxyStrictSSL`** and require the environment variable.

Open the **Remote Integrated Terminal** and run:

```bash
# Interactive terminal sessions
echo 'export NODE_TLS_REJECT_UNAUTHORIZED=0' >> ~/.bashrc

# CRITICAL: Non-interactive login shell profile read by VS Code Server daemon on boot
echo 'export NODE_TLS_REJECT_UNAUTHORIZED=0' >> ~/.profile
```

### Step 4 — Restart the Remote VS Code Server Daemon

VS Code **caches environment variables on startup**, so a restart is required:

1. Command Palette: `Ctrl + Shift + P`.
2. Select **Remote-SSH: Kill VS Code Server on Host...**.
3. Select the remote machine.
4. VS Code disconnects, wipes the old daemon, and reconnects with the new env vars active.

---

## Key Files

| File | Purpose |
|------|---------|
| `~/connect-vpn.sh` | Main VPN launcher: SAML auth + openconnect tunnel + DNS/HIP wiring. |
| `~/vpn-dns-wrapper.sh` | openconnect `--script`: fixes `systemd-resolved` DNS (search + routing domains). |
| `~/.config/openconnect/hipreport.sh` | HIP host-report script (downloaded if missing). |
| `~/.bashrc`, `~/.profile`, `~/.zshrc` | Added `NODE_TLS_REJECT_UNAUTHORIZED=0`. |
| `/etc/ssh/sshd_config` | SSH server configuration. |

---

## How to Use

### Connect to the VPN (foreground)

```bash
./connect-vpn.sh
```

The script will:
1. Launch SAML auth (browser remote login).
2. Extract the prelogin cookie.
3. Bring up the tunnel with DNS + HIP support.

### Connect in the background (recommended for daily use)

```bash
tmux new-session -d -s vpn "cd ~ && ./connect-vpn.sh"
# To view logs later:
tmux attach -t vpn
```

For a fully automatic, self-healing connection, use the systemd service described in [Running the VPN in the Background](#running-the-vpn-in-the-background-systemd-vs-tmux).

### Disconnect

```bash
# Ctrl+C in the openconnect/tmux terminal, or
sudo killall openconnect
```

---

## Verification Checklist

| Check | Command / Action | Expected Result |
| :--- | :--- | :--- |
| VPN Connected | `ip addr show tun0` | Shows assigned IP (e.g., `192.168.195.x`) |
| Internal DNS | `resolvectl query litellm.adeoaiengine.ecouncil.ae` | Returns internal IP address |
| HIP Report | Check `openconnect` output | No "WARNING: Server asked us to submit HIP report" |
| VS Code AI | Use OAI Copilot extension over SSH | Connects to internal endpoint without SSL errors |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Failed to obtain prelogin cookie` | SAML browser auth failed | Re-run `gpauth --browser remote --gateway vpn.ecouncil.ae`; check SSO session. |
| Hostnames not resolving (`resolvectl query ...` fails) | DNS not applied | Ensure `vpn-dns-wrapper.sh` ran; check `resolvectl status tun0`. |
| `resolvectl` stale settings | leftover DNS | The wrapper calls `resolvectl revert $IFACE` automatically on connect. |
| VPN drops / no TUN | firewall / UFW | `sudo ufw disable` during tests; re-enable + allow OpenSSH after. |
| Internal TLS errors | self-signed certs | `NODE_TLS_REJECT_UNAUTHORIZED=0` (already set). |

---

## Security Notes

- The `preloginCookie` is a **sensitive credential**. It is visible in shell history (`~/.bash_history`) and in `gpauth` output — consider clearing history or rotating if it leaks.
- `NODE_TLS_REJECT_UNAUTHORIZED=0` **disables TLS certificate validation** for Node processes — only acceptable in trusted internal environments. Revert for production.
- `connect-vpn.sh` runs `openconnect` with `sudo`; ensure the user has the needed sudoers rules and that the script files are not world-writable.

---

## Recommendation: tmux vs systemd — What Should You Use Now?

**For your situation, keep it simple and use `tmux` for now.**

Here's the honest trade-off:

### Why `tmux` is the right choice today

1. **SAML auth is interactive.** Your `gpauth` flow requires a browser login (SSO). That fundamentally breaks systemd's "fire-and-forget" automation — systemd can't type your credentials or click the SSO button. Every reconnect would still need a human.
2. **The cookie is short-lived.** The `preloginCookie` expires, so systemd's cached `/tmp/gp-auth.json` goes stale and the service fails on restart anyway.
3. **You get to a working state fastest.** `tmux` is a 1-line command that reuses your already-verified `connect-vpn.sh`.
4. **Zero risk of breaking your working setup.** No service file bugs, no sudoers changes needed.

### When to switch to `systemd`

Move to the systemd service (in [Running the VPN in the Background](#running-the-vpn-in-the-background-systemd-vs-tmux)) **only if/when**:

- You can get a **token-based / non-interactive** auth method from your IT team (this removes the biggest blocker).
- You need **auto-reconnect** across server reboots without any human intervention.
- You want **centralized logging** via `journalctl` and don't want to manage tmux sessions.

### The best of both worlds (recommended hybrid)

Use `tmux` for the interactive login, but keep the tunnel resilient:

```bash
# Start VPN in a detached tmux session that auto-restarts on crash
tmux new-session -d -s vpn "while true; do cd ~ && ./connect-vpn.sh; echo '[!] VPN exited, restarting in 10s...'; sleep 10; done"
tmux attach -t vpn
```

This gives you a **simple, manual login** (so you can still do SSO) **plus auto-reconnect** — without the complexity of systemd.

### Bottom line

> **Use `tmux` now.** It's simpler, works with your interactive SSO login, and gets you connected immediately. Move to `systemd` later only if your company provides non-interactive auth — otherwise the added complexity isn't worth it.

---

*Generated automatically from `~/.bash_history` and the two scripts in `~`.*