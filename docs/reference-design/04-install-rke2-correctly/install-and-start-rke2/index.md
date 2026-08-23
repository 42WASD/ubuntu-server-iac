---
order: 16
---

# Phase 16 — install and start RKE2

Install the pinned release:

```bash
curl -sfL https://get.rke2.io | \
  INSTALL_RKE2_VERSION='<EXACT_TESTED_RKE2_RELEASE>' sh -
```

Enable:

```bash
sudo systemctl enable rke2-server
```

Start:

```bash
sudo systemctl start rke2-server
```

Follow logs:

```bash
sudo journalctl -u rke2-server -f
```

In another shell:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get nodes -o wide
```

Wait for:

```text
alpha   Ready
```

Then:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get pods -A
```

Expected critical components should settle to:

```text
Running
Completed
```

not repeated:

```text
CrashLoopBackOff
ImagePullBackOff
Pending
```

---
