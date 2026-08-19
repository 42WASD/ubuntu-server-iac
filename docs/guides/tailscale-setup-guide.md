# Tailscale Setup Guide

**Tailnet owner:** `jya0@`
**Nodes:** `alpha` (primary), `beta` (secondary)

---

## Overview

Tailscale provides a **private mesh network** across all your machines, so `alpha` and `beta` can reach each other (and your laptops) securely without exposing SSH or other services to the public internet. Once a node joins the tailnet, it gets a stable `100.x.y.z` IP that works regardless of which network it is on.

This guide covers installing and joining both servers to your tailnet, verifying connectivity, and confirming the service starts automatically at boot.

## Current Node Map

| Node | Hostname | Tailscale IPv4 | Tailscale version | Status |
|------|----------|---------------|-------------------|--------|
| Primary | `alpha` | `100.112.202.47` | 1.102.2 | ✅ online |
| Secondary | `beta` | `100.73.126.73` | 1.102.2 | ✅ online |

Both nodes are in the same tailnet under the `jya0@` account.

---

## 1. Install Tailscale

Install on any Ubuntu node that does not yet have it:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

Verify the install:

```bash
tailscale version
```

> Requires network access to `tailscale.com`. If the box is behind a firewall/VPN, allow outbound to `tailscale.com` first.

---

## 2. Bring up the node and join the tailnet

Run as an admin (sudo) with a descriptive hostname:

```bash
sudo tailscale up --hostname=<HOSTNAME>
```

For our nodes:

```bash
# on alpha
sudo tailscale up --hostname=alpha

# on beta
sudo tailscale up --hostname=beta
```

You will see a one-time URL to authenticate (unless pre-auth'd):

```text
To authenticate, visit:

        https://login.tailscale.com/a/XXXX...

Success.
```

Open that URL in a browser logged into the `jya0@` account to approve the node. Once approved, the node joins the tailnet.

!!! note
    In this setup the auth completed automatically (pre-approved), so no manual browser step was needed. If it does **not** auto-approve, finish the login at the printed URL.

---

## 3. Verify the node is in the tailnet

On any joined node, list the network:

```bash
tailscale status
```

You should see both servers (plus any other devices):

```text
100.112.202.47  alpha   jya0@   linux   -
100.73.126.73   beta    jya0@   linux   -
```

Get the node's own IPv4:

```bash
tailscale ip -4
```

---

## 4. Confirm connectivity between alpha and beta

From `alpha`, ping `beta` over the tailnet:

```bash
ping -c 3 100.73.126.73
```

Expected:

```text
3 packets transmitted, 3 received, 0% packet loss
```

From `beta`, ping `alpha`:

```bash
ping -c 3 100.112.202.47
```

> The two nodes connect **directly** when possible (same LAN) and fall back to a DERP relay only when necessary. On the same home LAN you will typically see a direct connection.

---

## 5. Confirm Tailscale starts at boot (persistence)

Tailscale's daemon is `tailscaled` and is managed by systemd. Confirm it is enabled to start at boot and is currently running:

```bash
systemctl is-enabled tailscaled   # -> enabled
systemctl is-active tailscaled    # -> active
```

The node's identity is persisted in `/var/lib/tailscale/tailscaled.state` so it **automatically rejoins the tailnet after a reboot without re-login**.

Verify the persisted state exists:

```bash
sudo ls -la /var/lib/tailscale/tailscaled.state
```

Expected: a `tailscaled.state` file owned by `root`.

---

## 6. Check node key expiry

Node keys are not permanent. Check when the key expires:

```bash
tailscale status --json | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['Self']['KeyExpiry'])"
```

On `beta` this currently reports `2027-02-15`, so no action is needed for several months. When a key approaches expiry, you can re-authenticate or use an auth key for fully unattended rejoin.

!!! warning
    When the key expires the node drops off the tailnet until re-authenticated. Set a reminder before the expiry date.

---

## Reference: persistent service behaviour

| Behaviour | Detail |
|-----------|--------|
| Starts at boot | ✅ `tailscaled` is `enabled` |
| Rejoins automatically | ✅ identity stored in `/var/lib/tailscale/tailscaled.state` |
| Survives reboot | ✅ no manual `tailscale up` needed |
| Requires network | Outbound to `tailscale.com` / DERP relay as needed |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `state: NeedsLogin` | `sudo tailscale up --hostname=<node>` again and authenticate |
| Node not visible on peer | Check both nodes can reach the internet; `tailscale status` on each |
| Slow / relayed connection on LAN | Should be direct; verify they are on the same network |
| Service not starting at boot | `sudo systemctl enable tailscaled` |

---

## Related

- [SSH Connection Guide](ssh-connection-guide.md) — stable SSH over the tailnet / VPN.
- [Beta GPU Driver Guide](beta-gpu-driver-guide.md) — hardware status of `beta`.