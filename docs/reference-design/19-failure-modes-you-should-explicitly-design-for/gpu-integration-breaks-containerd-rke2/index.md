---
order: 7
---

# GPU integration breaks containerd/RKE2

This is why GPU is a later phase.

Mitigation:

```text
base RKE2 proven first
etcd snapshot
host driver proven
follow RKE2-specific GPU instructions
one change at a time
keep GPU workload non-critical until validated
```

---
