---
phase: 04-install-rke2-correctly/07-26-phase-17-admin-kubeconfig-and-cli-convenience
---
# Phase 17 — admin kubeconfig and CLI convenience

**Intent:** give the **platform admin only** (`jyao`) the RKE2 admin kubeconfig
and expose `kubectl` / `crictl` for day-to-day admin convenience. Developers do
**not** get this file — they receive their own identities/kubeconfigs later
(Phase 26 RBAC).

## 17.1 Admin kubeconfig

Copied the root-only RKE2 admin kubeconfig into the admin user's home:

```bash
mkdir -p /home/jyao/.kube
sudo cp /etc/rancher/rke2/rke2.yaml /home/jyao/.kube/config
sudo chown -R jyao:jyao /home/jyao/.kube
chmod 600 /home/jyao/.kube/config
```

## 17.2 Point the kubeconfig at the management address

RKE2 generates the admin kubeconfig with `server: https://127.0.0.1:6443`.
The reference design says to change it to the management address so it works
remotely.

> **Design decision — MagicDNS name, not the raw IP.** The reference uses
> `<ALPHA_TAILSCALE_IP>`, but consistent with Phase 14 we used the stable
> Tailscale MagicDNS hostname (`alpha.taild82ced.ts.net`) instead. This name is
> already in the serving certificate's `tls-san`, and unlike the 100.x IP it
> cannot be reallocated. So `kubectl` presents a valid cert and keeps working
> across Tailscale address changes.

```bash
sed -i 's|https://127.0.0.1:6443|https://alpha.taild82ced.ts.net:6443|' /home/jyao/.kube/config
```

Result: `server: https://alpha.taild82ced.ts.net:6443`.

## 17.3 Expose bundled CLI tools

```bash
sudo ln -sf /var/lib/rancher/rke2/bin/kubectl /usr/local/bin/kubectl
sudo ln -sf /var/lib/rancher/rke2/bin/crictl /usr/local/bin/crictl
```

`crictl` also needed to know RKE2's non-standard containerd socket. Created
`/etc/crictl.yaml`:

```yaml
runtime-endpoint: unix:///run/k3s/containerd/containerd.sock
image-endpoint: unix:///run/k3s/containerd/containerd.sock
timeout: 10
debug: false
```

## 17.4 Verify

```bash
export KUBECONFIG=/home/jyao/.kube/config
kubectl get nodes
```

Observed:

```text
NAME    STATUS   ROLES                AGE   VERSION          CONTAINER-RUNTIME
alpha   Ready    control-plane,etcd   16m   v1.36.3+rke2r1   containerd://2.3.3-k3s1
```

`kubectl get nodes` succeeds over the MagicDNS address with a valid cert.
`sudo crictl version` reports containerd `v2.3.3-k3s1`.

## 17.5 What was implemented (Ansible)

- `rke2_server` defaults: `rke2_admin_user`, `rke2_admin_kubeconfig_server`
  (MagicDNS), `rke2_admin_kubeconfig_source`, `rke2_admin_kubeconfig_dest`.
- `tasks/main.yml`: create `kubectl` / `crictl` symlinks, write
  `/etc/crictl.yaml`, copy + own the admin kubeconfig, and rewrite its `server`
  to the management hostname.

## 17.6 Result

Admin access over Tailscale with a valid serving certificate is confirmed.
Developers keep their own identities per Phase 26.