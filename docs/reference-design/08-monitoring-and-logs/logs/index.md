# logs

Deploy:

```text
Loki
Grafana Alloy
```

Do not keep every debug log forever.

Initial policy:

```text
Kubernetes centralized logs:
  7-14 days

high-volume debug:
  shorter

security/audit logs:
  longer, preferably off-host
```

The root filesystem still gets local container/system logs.

Central logging does not remove the need for:

```text
kubelet log rotation
journald limits
application log discipline
```

---
