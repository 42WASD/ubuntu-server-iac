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

---
