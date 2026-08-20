---
phase: 04-install-rke2-correctly/08-27-phase-18-verify-reboot-recovery-now-not-later
---
# Phase 18 — verify reboot recovery now, not later

**Intent:** prove that a normal reboot brings the whole platform back with
**zero manual intervention** — no manual `docker start`, no manual `kubectl
apply`, no manual CNI repair (Checkpoint 11). Because the cluster state lives
in etcd on disk, workloads (like the `demo-meme` Deployment) are recreated by
the controllers automatically.

## 18.1 Pre-reboot baseline

Captured immediately before rebooting:

```bash
export KUBECONFIG=/home/jyao/.kube/config
systemctl is-active rke2-server      # active
kubectl get nodes                     # alpha Ready control-plane,etcd
kubectl get pods -A                   # all Running / Completed
kubectl -n demo-meme get pods         # meme-site-* 1/1 Running
uptime -p                             # up 23 hours, 49 minutes
```

Baseline was clean: control plane pods (`kube-apiserver`, `etcd`,
`kube-scheduler`, `kube-controller-manager`), Cilium + operator, CoreDNS,
Traefik, metrics-server, snapshot-controller, and the `demo-meme` app were all
healthy.

## 18.2 Reboot

```bash
sudo reboot
```

SSH re-established once the host was back.

## 18.3 Post-reboot recovery check

```bash
systemctl is-active rke2-server
kubectl get nodes
kubectl get pods -A
kubectl -n demo-meme get pods
```

Wait for reconciliation, then record boot time:

```bash
systemd-analyze
systemd-analyze blame | head -30
```

## 18.4 Checkpoint 1

Recovery requires:

```text
zero manual "docker start"
zero manual "kubectl apply"
zero manual CNI repair
```

The `demo-meme` pod must be recreated by the Deployment controller, and the
node must return to `Ready`.

## 18.5 Post-reboot observations (live)

Verified after the host came back:

```bash
uptime -p                 # up 19 minutes  -> reboot confirmed
systemctl is-enabled rke2-server   # enabled
systemctl is-active rke2-server    # active
systemctl --failed --no-legend | wc -l   # 0
kubectl get nodes         # alpha Ready
kubectl get pods -A       # 14 Running, 8 Completed
```

- Node `alpha` `Ready`, `containerd://2.3.3-k3s1`, Ubuntu 26.04.
- `rke2-server` **enabled** and **active**; **0 failed systemd units**.

## 18.6 `demo-meme` survivor probe

```bash
kubectl -n demo-meme get pods
```

```text
NAME-                         READY   STATUS    RESTARTS      AGE
meme-site-7486bc7c98-cqkg4   1/1     Running   1 (19m ago)   26m
```

`RESTARTS 1 (19m ago)` matches the reboot window — the kubelet recreated the
pod by itself. Deployment UID unchanged (`d6104ebf-…`), so it is the same
Deployment (no manual re-apply). Still serving after reboot:

```bash
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://10.43.247.243/
curl -s -o /dev/null -w 'HTTP %{http_code} %{content_type}\n' http://10.43.247.243/meme.svg
```

```text
HTTP 200
HTTP 200 image/svg+xml
```

## 18.7 Boot timing

```bash
systemd-analyze time
```

```text
Startup finished in 2min 8.556s (firmware) + 1.515s (loader) + 2.650s (kernel) +
 7.480s (initrd) + 9.590s (userspace) = 2min 29.793s
graphical.target reached after 9.328s in userspace.
```

Boot ID after reboot: `064aa60d-d349-4258-add6-3a6da3c426c4`.

## 18.8 Result — Checkpoint 11 passed

The reboot required **zero** manual container starts, **zero** manual
`kubectl apply`, and **zero** manual CNI repair. Node, add-ons, and the
`demo-meme` tenant all recovered automatically. This closes the reboot-risk
gate before adding more components.