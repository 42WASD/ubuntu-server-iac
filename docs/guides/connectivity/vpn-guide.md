# VPN Connection Guide

This guide covers connecting `alpha` to the **corporate VPN** — GlobalProtect (`vpn.ecouncil.ae`) with **SAML** authentication — and keeping the tunnel stable and persistent.

**Host:** `alpha` · **User:** `jyao`

## Overview

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

### Accessing the remote-browser auth URL over Tailscale

`gpauth --browser remote` binds its one-shot auth server to the **local LAN IP**
(the IP used to reach 1.1.1.1) and prints `http://<lan-ip>:<port>/<id>`. A
socket bound to the LAN IP is **not** reachable at the Tailscale IP, so the
printed link fails if you connect from another machine over Tailscale. There is
**no `gpauth` flag** to bind `0.0.0.0`.

`connect-vpn.sh` prefers the wrapper `scripts/vpn/gpauth-broadcast.sh` (falling
back to stock `gpauth`). The wrapper:

- Runs `gpauth --browser remote` unchanged (stdout JSON, stdin pass-through so
  you can paste the auth callback).
- Watches stderr for the printed URL and extracts the random port + auth-id.
- Starts a **`socat` forwarder bound to the Tailscale IP** (`bind=<ts-ip>`) on
  that same port, relaying to gpauth's LAN-bound `ip:port`. This needs **no
  root** (unlike the earlier iptables DNAT approach).
- Prints a Tailscale-friendly URL:

  ```text
  ================================================================
  ==== Auth URL (reachable via Tailscale / any interface) ====
      http://<ts-ip>:<port>/<auth-id>
  ============================================================
  ```

**Why bind the Tailscale IP specifically (not `0.0.0.0`):** gpauth's auth server
already holds that port on the LAN IP, and socat binding `0.0.0.0` (wildcard)
conflicts with it (`Address already in use`). Binding to the distinct Tailscale
IP on the same port avoids the conflict and still makes the URL reachable on
both LAN and Tailscale.

The forwarder is cleaned up automatically when the wrapper exits. Requires
`socat` to be installed.

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

## DNS Fix for systemd-resolved

Created `vpn-dns-wrapper.sh`, used as the `--script` argument for `openconnect`. On `connect`/`reconnect` it:

- Calls the original `/usr/share/vpnc-scripts/vpnc-script` to set up routes and the TUN interface.
- Clears stale settings (`resolvectl revert`).
- Pushes VPN-internal DNS servers (`INTERNAL_IP4_DNS`).
- Adds VPN domains as both **search domains** and **routing domains** (`~` prefix) for split-DNS.
- On `disconnect`, reverts DNS.

Verified with `resolvectl query litellm.adeoaiengine.ecouncil.ae`.

## HIP (Host Health) Script

The gateway requires a HIP report. `connect-vpn.sh` looks for `hipreport.sh` under `/usr /etc /opt` and `~/.config/openconnect`; if absent, it downloads the official script from the openconnect GitLab repo into `~/.config/openconnect/hipreport.sh`.

## Scripts

| File | Purpose |
|------|---------|
| `scripts/vpn/connect-vpn.sh` | Main VPN launcher |
| `scripts/vpn/vpn-dns-wrapper.sh` | openconnect `--script`: DNS fix |
| `scripts/vpn/vpn-persist.sh` | VPN persistence loop |
| `scripts/vpn/gpauth-broadcast.sh` | `gpauth --browser remote` wrapper that makes the auth URL reachable via Tailscale (socat, no root) |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Failed to obtain prelogin cookie` | SAML auth failed | Re-run `gpauth`; check SSO session |
| Hostnames not resolving | DNS not applied | Check `resolvectl status tun0` |
| VPN drops | firewall/UFW | Allow OpenSSH, re-enable UFW |
| Internal TLS errors | self-signed certs | `NODE_TLS_REJECT_UNAUTHORIZED=0` |