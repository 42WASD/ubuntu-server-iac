---
order: 5
---

# CPU-pressure runbook

Inspect:

```bash
uptime
mpstat -P ALL 1
pidstat 1
systemd-cgtop
kubectl top pods -A --sort-by=cpu
```

If host developer is responsible:

```text
user slice limit should contain it
```

If build is responsible:

```text
it should not be running on alpha
```

If Kubernetes tenant is responsible:

```text
requests/limits/quota should contain it
```

---
