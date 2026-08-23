---
order: 0
---

# Upgrade order

Do not upgrade every layer in one maintenance window.

Recommended order per change set:

```text
1. backup / etcd snapshot
2. Git commit for intended version
3. host package/kernel change if required
4. reboot if required
5. RKE2 minor/patch
6. verify Cilium/Traefik
7. platform controllers
8. tenant workloads
9. GPU integration last
```

One major variable at a time.

---
