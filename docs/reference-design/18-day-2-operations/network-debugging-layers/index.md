---
order: 6
---

# Network-debugging layers

Debug in this order:

```text
1. host route/DNS
2. Tailscale
3. RKE2 node health
4. Cilium
5. Kubernetes Service
6. NetworkPolicy
7. Traefik/Gateway
8. Cloudflare
```

Do not start by disabling Cilium or the firewall.

Example commands:

```bash
ip route
resolvectl status
tailscale status

kubectl get nodes
kubectl -n kube-system get pods

kubectl get svc -A
kubectl get networkpolicy -A

kubectl -n kube-system logs <cilium-pod>
kubectl -n kube-system logs <traefik-pod>
```

---
