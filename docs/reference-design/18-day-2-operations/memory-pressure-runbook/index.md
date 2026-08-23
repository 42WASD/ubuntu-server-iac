---
order: 4
---

# Memory-pressure runbook

Inspect:

```bash
free -h
ps aux --sort=-%mem | head -30
systemd-cgtop
kubectl top nodes
kubectl top pods -A --sort-by=memory
dmesg | grep -i -E 'oom|killed process'
```

Determine:

```text
host user process?
Kubernetes Pod?
kernel cache?
GPU-related process?
```

Do not solve every memory problem by increasing `MemoryMax`.

---
