# alert before things are full

Alert thresholds should include:

```text
root > 70% warning
root > 85% critical

RKE2 data filesystem > 70/85%

NVMe/HDD VG free capacity low

memory available < 16 GiB warning
memory available < 8 GiB critical

node NotReady

Cilium unavailable

API server unavailable

etcd snapshot failure

PVC approaching full

GPU temperature / utilization later

WireGuard relay loss later
```

The important alert is not:

```text
disk = 100%
```

because by then the platform is already in trouble.

---
