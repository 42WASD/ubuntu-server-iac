---
order: 4
---

# Cilium breaks after upgrade

Mitigation:

```text
pin RKE2
read bundled Cilium release notes
snapshot etcd
change one platform layer at a time
keep console/Tailscale access to host
do not simultaneously alter nftables + Cilium + RKE2
```

---
