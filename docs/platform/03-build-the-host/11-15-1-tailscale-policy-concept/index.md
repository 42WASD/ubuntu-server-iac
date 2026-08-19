# Tailscale policy concept

Your tailnet policy should distinguish:

```text
platform-admins
developers
build-nodes
relay-nodes
```

Conceptually:

```text
platform-admins
    -> alpha:22
    -> alpha:6443
    -> admin UIs

developers
    -> alpha:22
    -> alpha:6443
    -> only where Kubernetes RBAC allows after connection

build-nodes
    -> registry
    -> BuildKit-specific paths

random tailnet devices
    -> no implicit platform access
```

Tailscale controls **network reachability**.

Kubernetes RBAC still controls **Kubernetes authorization**.

Do not confuse them.

## Checkpoint 5

From an authorized laptop:

```bash
ping <ALPHA_TAILSCALE_IP>
ssh jyao@<ALPHA_TAILSCALE_IP>
```

Both must work before tightening public/LAN SSH access.

---
