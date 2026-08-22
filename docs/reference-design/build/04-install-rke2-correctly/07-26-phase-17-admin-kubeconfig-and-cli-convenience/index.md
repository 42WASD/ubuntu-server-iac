# Phase 17 — admin kubeconfig and CLI convenience

Do not give every developer the RKE2 admin kubeconfig.

For `jyao` only:

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/rke2/rke2.yaml ~/.kube/config
sudo chown "$USER:$USER" ~/.kube/config
chmod 600 ~/.kube/config
```

The kubeconfig's server may point at localhost.

Change it to the management IP if the admin uses it remotely:

```bash
sed -i "s/127.0.0.1/<ALPHA_TAILSCALE_IP>/" ~/.kube/config
```

Expose RKE2's bundled kubectl for admin convenience:

```bash
sudo ln -sf /var/lib/rancher/rke2/bin/kubectl /usr/local/bin/kubectl
sudo ln -sf /var/lib/rancher/rke2/bin/crictl /usr/local/bin/crictl
```

Verify:

```bash
kubectl get nodes
```

Normal developers will later get **their own identities/kubeconfigs**, not this file.

## k9s (terminal cluster UI, system-wide)

k9s is a companion terminal UI to `kubectl`. It is **not** in the Ubuntu apt
archive, so the `rke2_server` role installs the official pinned `.deb`
(checksum-verified) into `/usr/bin/k9s` — available to every user, each of
whom runs it against their **own** OIDC kubeconfig (Phase 27).

- Pin: `rke2_k9s_version` (default `v0.51.0`), with the exact `.deb` URL and
  its sha256 in `rke2_k9s_deb_url` / `rke2_k9s_deb_checksum`.
- Install: `get_url` (asserting the checksum) → `apt: deb:` → remove the
  staged `.deb`.
- Because it is a per-user CLI on top of the shared kubeconfig, no privileged
  state is held; each developer's access is still bounded by their RBAC groups
  (Phase 26) and the OIDC identity they log in with.

```bash
k9s                      # default context
k9s --context alpha-dev  # explicit tenant context
```

---
