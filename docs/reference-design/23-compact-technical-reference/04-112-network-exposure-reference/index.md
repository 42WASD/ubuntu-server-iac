# Network exposure reference

```text
22/tcp SSH
    Tailscale only

6443/tcp Kubernetes API
    Tailscale / RKE2 nodes only

9345/tcp RKE2 supervisor
    RKE2 nodes only

10250/tcp kubelet
    RKE2 nodes/metrics path only

public 80/443
    ideally Cloudflare path, not home-router direct exposure

game ports
    VPS relay -> WireGuard -> explicit Kubernetes/game service
```

When additional RKE2 nodes join, follow RKE2's current Cilium-specific node-to-node port requirements and restrict those ports to the node network only.

---
