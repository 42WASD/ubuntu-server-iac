# Ubuntu Server IAC — Engineering Documentation

Welcome to the central knowledge base for the **ubuntu-server-iac** project. This documents the setup, configuration, and operation of the Ubuntu server (`alpha`) and its associated infrastructure-as-code scripts.

Use the top navigation tabs to explore the setup guide, SSH configuration, and operational runbooks.

!!! note "Status"
    This documentation is actively maintained. Edits made to `main` automatically deploy to GitHub Pages.

## About This Server

| Item | Value |
|------|-------|
| Hostname | `alpha` |
| Motherboard | HUANANZHI H12D-8D (Rev V2.0) |
| CPU | AMD EPYC 7742 64-Core |
| GPUs | 2 × NVIDIA RTX 3090 (GA102) |
| OS | Ubuntu Server 26.04 LTS |
| Access | SSH (macOS client) + Tailscale + Corporate VPN |

## Quick Links

- [Server Setup Guide](setup/server-setup-guide.md)
- [SSH Connection Guide](guides/ssh-connection-guide.md)
- [Source Code Repository](https://github.com/42WASD/ubuntu-server-iac)

## Operations Summary

- **VPN**: GlobalProtect connection via `connect-vpn.sh` (SAML auth).
- **Monitoring**: `lm-sensors` + `btop` for hardware temperature/usage.
- **GPU Compute**: NVIDIA driver `nvidia-driver-595-server` (proprietary).
- **Docs**: This MkDocs site, deployed via GitHub Actions.