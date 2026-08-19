# SSH Connection Guide

**User:** `jyao`
**Host:** `alpha`
**Environment:** macOS (client) → Linux (Ubuntu Server) via SSH

---

## Table of Contents

1. [Overview](#overview)
2. [SSH Config Location](#ssh-config-location)
3. [Keeping the Connection Alive](#keeping-the-connection-alive)
4. [Other Useful SSH Settings](#other-useful-ssh-settings)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide documents the SSH client configuration used to connect from the local **macOS** workstation to the remote Linux server (`alpha`). The main goal is to keep SSH connections **stable during inactivity**, which is common when working over a VPN or behind NAT/firewall idle-timeouts.

---

## SSH Config Location

The SSH **client** config lives on the machine you SSH **from** — i.e. the **macOS** workstation, **not** the remote server.

| File | Location | Purpose |
|------|----------|---------|
| Client config | `~/.ssh/config` (macOS) | Client-side settings (keep-alive, aliases, keys). |
| Server config | `/etc/ssh/sshd_config` (remote) | Server-side settings (on the Linux host). |

Edit the client config with:

```bash
nano ~/.ssh/config
```

---

## Keeping the Connection Alive

To prevent idle SSH sessions from being dropped, add a keep-alive rule to `~/.ssh/config` on macOS.

### Apply to all hosts

```ssh_config
Host *
  # Keep SSH connection alive during inactivity
  ServerAliveInterval 30
  ServerAliveCountMax 3
  TCPKeepAlive yes
```

### Apply to a specific host

```ssh_config
Host alpha
  HostName alpha
  User jyao
  ServerAliveInterval 30
  ServerAliveCountMax 3
  TCPKeepAlive yes
```

### What each setting does

| Setting | Value | Purpose |
|---------|-------|---------|
| `ServerAliveInterval` | `30` | Sends an encrypted keep-alive message through the tunnel every 30 seconds when idle. This is the key setting that prevents drops. |
| `ServerAliveCountMax` | `3` | Drops the connection after 3 unacknowledged keep-alives (~90s), so SSH fails fast instead of hanging. |
| `TCPKeepAlive` | `yes` | Enables TCP-level keepalive on the underlying socket as an extra layer of protection. |

### Applying the change

- The settings take effect for **new** SSH connections — no daemon restart needed.
- Existing already-open sessions won't pick them up until you reconnect.
- Use `Host *` to apply globally, or scope the settings under a specific `Host` block to target only certain servers.

---

## Other Useful SSH Settings

The following optional settings can improve SSH reliability and convenience:

```ssh_config
Host *
  # Connection multiplexing: reuse an open connection to the same host
  ControlMaster auto
  ControlPath ~/.ssh/controlmasters/%r@%h:%p
  ControlPersist 10m

  # Avoid prompts about changed host keys
  # (use with caution — only if you trust the network)
  # StrictHostKeyChecking accept-new
```

| Setting | Purpose |
|---------|---------|
| `ControlMaster auto` | Enables connection multiplexing. |
| `ControlPath ~/.ssh/controlmasters/%r@%h:%p` | Socket location for the shared control connection. |
| `ControlPersist 10m` | Keeps the master connection alive for 10 minutes after the last session closes. |

> ⚠️ Create the control socket directory if you use multiplexing: `mkdir -p ~/.ssh/controlmasters && chmod 700 ~/.ssh/controlmasters`.

---

## Verification

Confirm the keep-alive settings are active for a host:

```bash
ssh -G alpha | grep -Ei 'serveraliveinterval|serveralivecountmax|tcpkeepalive'
```

Expected output:

```
serveraliveinterval 30
serveralivecountmax 3
tcpkeepalive yes
```

Also verify the config file parses without errors:

```bash
ssh -T -o BatchMode=yes alpha 2>&1 | head
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Connection drops after idle time | Firewall/NAT idle timeout | Ensure `ServerAliveInterval` is set and reconnect. |
| Keep-alive settings not applied | Editing server config instead of client | Edit `~/.ssh/config` on the **macOS** machine, not on the server. |
| Old session still drops | Existing session predates the change | Reconnect to pick up the new settings. |
| `Bad owner or permissions` | Wrong file mode | Run `chmod 600 ~/.ssh/config`. |

---

*SSH connection configuration for `jyao` — generated 2026-08-19.*