---
order: 1
---

# RKE2 upgrade checklist

Before:

```bash
kubectl get nodes
kubectl get pods -A
sudo rke2 etcd-snapshot save --name before-rke2-upgrade
```

Read:

```text
RKE2 release notes
Kubernetes urgent upgrade notes
Cilium version change
Traefik version change
containerd version change
known issues
```

After:

```bash
kubectl get nodes
kubectl get pods -A
kubectl get events -A --sort-by=.lastTimestamp | tail -100
```

Test:

```text
DNS
HTTP ingress
PVC mount
Argo reconciliation
tenant RBAC
NetworkPolicy
GPU if enabled
```

---
