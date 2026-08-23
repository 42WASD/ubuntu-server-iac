---
phase: 04-install-rke2-correctly/install-and-start-rke2/inspect-cilium
---

# Phase 25.1 — inspect Cilium

**Intent:** verify the bundled Cilium CNI is running as expected, that
kube-proxy is genuinely disabled (using Cilium's replacement), and that Pod
DNS / service networking works inside the cluster.

## 25.1.1 Cilium pods

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get pods -o wide | grep -i cilium
```

Observed:

```text
cilium-ks259                             1/1   Running    12m   192.168.8.132  alpha
cilium-operator-8569876bb4-mj27t         1/1   Running    12m   192.168.8.132  alpha
helm-install-rke2-cilium-dc76p           0/1   Completed  3m37s 192.168.8.132  alpha
```

Cilium agent daemonset is `Running`; the operator is `Running` (single
replica, per Phase 15 operator scaling); the helm install job `Completed`.

## 25.1.2 Daemonsets

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get daemonset
```

Observed: `cilium` (1/1 Ready) and `rke2-traefik` (1/1 Ready).

## 25.1.3 No kube-proxy DaemonSet

Because we set `disable-kube-proxy: true` (Phase 14) and
`kubeProxyReplacement: true` (Phase 15), kube-proxy must **not** exist:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  -n kube-system get ds kube-proxy
```

Expected `NotFound`; observed:

```text
Error from server (NotFound): daemonsets.apps "kube-proxy" not found
```

✅ Confirms Cilium's eBPF kube-proxy replacement is in use.

## 25.1.4 Service networking / DNS inside a Pod

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  run dns-test --rm -it --restart=Never --image=busybox:1.36 \
  -- nslookup kubernetes.default.svc.cluster.local
```

Observed:

```text
Server:    10.43.0.10
Address:   10.43.0.10:53

Name:   kubernetes.default.svc.cluster.local
Address: 10.43.0.1
```

✅ Cluster DNS (`10.43.0.10`) resolves the Kubernetes service (`10.43.0.1`),
proving service networking + DNS work inside a Pod.

## 25.1.5 Result

All checks pass. Combined with Phase 16, **Checkpoint 10 (base cluster gate)**
is satisfied: `alpha Ready`, CoreDNS/Cilium/Traefik/metrics-server running,
DNS + service networking work, no unexplained restarts. A state snapshot was
captured to `~/platform-audit/k8s-first-healthy.txt`.