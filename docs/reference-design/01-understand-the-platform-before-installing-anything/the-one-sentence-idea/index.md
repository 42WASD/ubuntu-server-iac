# The one-sentence idea

Build the machine in layers and give each layer **one job**:

```text
Ubuntu Autoinstall
    -> installs/reinstalls the OS predictably

Ansible
    -> configures Linux: users, storage, SSH, Tailscale, limits, packages, RKE2

RKE2
    -> runs Kubernetes

Cilium
    -> pod networking + network policy

Traefik
    -> HTTP/HTTPS ingress into Kubernetes

Argo CD
    -> makes Kubernetes match Git

OpenEBS LocalPV LVM
    -> provisions local persistent volumes from host LVM VGs

Kyverno + Pod Security Admission
    -> prevents unsafe tenant workloads

Prometheus/Grafana/Loki/Alloy
    -> tells you what the platform is doing

Harbor
    -> stores container images

Remote BuildKit on build01
    -> performs expensive container builds away from alpha

Cloudflare
    -> public web edge / tunnel / Access

UAE relay VPS + WireGuard
    -> public game TCP/UDP path when home networking cannot expose it cleanly

OpenTofu
    -> creates external infrastructure such as Cloudflare/OCI resources
```

The critical design rule is:

```text
INSTALL != CONFIGURE != DEPLOY != BUILD != EXPOSE != BACK UP
```

Do not make one giant shell script perform all six jobs.

---
