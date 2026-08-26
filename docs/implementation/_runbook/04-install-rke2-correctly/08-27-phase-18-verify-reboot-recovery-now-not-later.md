---
phase: 04-install-rke2-correctly/verify-reboot-recovery-now-not-later
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

## 18.9 Follow-up incident — DHCP IP drift took the cluster down

**Symptom:** `rke2-server` stuck in `activating`, `kubectl` unresponsive.
`journalctl -u rke2-server` showed the etcd peer mismatch:

```text
Found [alpha-49ad8379=https://192.168.8.132:2380], expect:
  ... https://192.168.8.137:2380
```

**Root cause:** `enp193s0` was on **DHCP** and the lease moved across reboots
(`192.168.8.132` → `192.168.8.137`). RKE2 derives its etcd peer/advertise URLs
from the node IP, so an IP change left etcd's membership pointing at an
address the node no longer held.

**Fix (do this on any RKE2 server running on DHCP):**

1. Pin the LAN interface to a **static, uncommon** address so it can't collide
   with the DHCP pool — `192.168.8.240` (high range, avoids `.132–.150` DHCP
   range) — in `/etc/netplan/00-installer-config.yaml` (`dhcp4: false`), then
   `sudo netplan apply`.
2. Pin RKE2's `node-ip` to the same address so RKE2 is decoupled from the
   interface lease entirely. Append to `/etc/rancher/rke2/config.yaml`:

```yaml
# Pinned node-ip to the static LAN address (192.168.8.240) so the etcd
# peer/advertise URLs no longer depend on the DHCP lease. See netplan.
node-ip: 192.168.8.240
```

3. Reconcile the already-booted etcd. For a **single-node** control plane the
   recovery is a cluster-reset (forgets stale peers, becomes sole member again
   using the current node-ip, keeps existing data dir):

```bash
sudo systemctl stop rke2-server
sudo rke2 server --cluster-reset            # resets membership, backs up certs
sudo systemctl start rke2-server
```

4. Verify etcd now advertises the new address and the node is healthy:

```bash
sudo cat /var/lib/rancher/rke2/server/db/etcd/config | grep -E 'advertise|initial-cluster'
# expect: https://192.168.8.240:2380  (NOT the old lease)
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
kubectl get nodes -o wide          # alpha Ready, INTERNAL-IP 192.168.8.240
kubectl get pods -A | grep -vE 'Running|Completed'
```

**Verified (live):** etcd config regenerated with `initial-cluster:
alpha-107afd20=https://192.168.8.240:2380` and
`advertise-client-urls: https://192.168.8.240:2379`; `alpha` returned to
`Ready` at `192.168.8.240`; Cilium, Traefik, CoreDNS, and Kyverno all recovered;
the `42wasd` app returned to `1/1 Running` and served `HTTP 200` through the
ingress. The DHCP IP drift is now impossible because the address is static in
both netplan and `node-ip`.