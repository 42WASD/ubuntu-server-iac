# metrics stack

Install through Argo CD:

```text
Prometheus Operator / kube-prometheus-stack
Grafana
node-exporter
kube-state-metrics
Alertmanager
```

> **As-deployed note (2026-08-29):** the stack is running (chart
> `kube-prometheus-stack-88.5.4`, release `prometheus`, ns `monitoring`) but
> was installed via **plain Helm**, not Argo CD, and has **no PVCs / no
> retention override / no Loki** yet. See the metrics-stack runbook for the
> live state and follow-ups.

Start small.

Single-node default targets:

```text
Prometheus PVC: 50-100 GiB
retention:      10-15 days initially
Grafana PVC:    small
Alertmanager:   small
```

Do not allocate 500 GiB because "we have disk."

First measure ingestion.

Track:

```text
host CPU
load average
host memory
memory pressure
filesystem capacity
filesystem inode capacity
disk latency
NVMe SMART
HDD SMART
Pod CPU/RAM
restarts
OOM kills
pending Pods
PVC usage
etcd health
API latency
Cilium health
Traefik 4xx/5xx
```

---
