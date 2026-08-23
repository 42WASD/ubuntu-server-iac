---
order: 6
---

# Phase 6 — Tailscale private management path

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
