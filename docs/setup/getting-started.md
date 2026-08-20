# Getting Started

Follow this onboarding workflow to set up your local development environment and connect to the `alpha` server.

## Prerequisites

- macOS or Linux workstation.
- SSH access to `alpha` (see the [SSH Connection guide](../guides/connectivity/ssh-connection-guide.md)).
- Corporate VPN access for internal endpoints.

## Connect to the Server

```bash
ssh alpha
```

## First-Time Server Tasks

1. **Update packages**
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   ```
2. **Install monitoring tools**
   ```bash
   sudo apt install -y lm-sensors btop
   ```
3. **Verify hardware**
   ```bash
   lspci | grep -i nvidia   # GPUs
   sensors                  # temperatures
   ```

## The VPN

To connect to the corporate VPN (see the full [VPN Connection guide](../guides/connectivity/vpn-guide.md)):

```bash
tmux new-session -d -s vpn "cd ~ && ./connect-vpn.sh"
tmux attach -t vpn
```

## Docker

```bash
docker compose up -d
```

---

Now that you're connected, explore the [Server Setup Guide](server-setup-guide.md) for full configuration details.