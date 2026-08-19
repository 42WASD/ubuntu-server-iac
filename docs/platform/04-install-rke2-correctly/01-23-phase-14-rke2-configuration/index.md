# Phase 14 — RKE2 configuration

Create:

```bash
sudo mkdir -p /etc/rancher/rke2
sudoedit /etc/rancher/rke2/config.yaml
```

Start with:

```yaml
node-name: alpha

cni: cilium
ingress-controller: traefik

# We will use Cilium's kube-proxy replacement.
disable-kube-proxy: true

# Keep the API certificate usable through the management address.
tls-san:
  - "<ALPHA_TAILSCALE_IP>"

# Admin kubeconfig remains root/platform-admin controlled.
write-kubeconfig-mode: "0640"

# etcd snapshots
etcd-snapshot-schedule-cron: "0 */6 * * *"
etcd-snapshot-retention: 12
etcd-snapshot-compress: true

# Basic labels for future scheduling.
node-label:
  - "platform.example.com/role=core"
  - "platform.example.com/storage-nvme=true"
  - "platform.example.com/storage-hdd=true"
  - "platform.example.com/gpu=true"
```

Do **not** put the cluster token in Git.

---
