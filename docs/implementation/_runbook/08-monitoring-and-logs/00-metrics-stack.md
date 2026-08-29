---
phase: 08-monitoring-and-logs/metrics-stack
---

# Metrics stack — kube-prometheus-stack (deployed 2026-08-24)

**Intent:** platform metrics baseline per Part VIII. This runbook records the
**as-deployed** state discovered during the 2026-08-29 doc-reality sweep —
the stack was installed via Helm directly (not yet under Argo CD), which
diverges from the reference page's "install through Argo CD" intent. The
migration to Argo is noted as follow-up work below.

## Live state (verified 2026-08-29)

- Namespace `monitoring`, Helm release **`prometheus`**, chart
  **`kube-prometheus-stack-88.5.4`** (Grafana chart 12.11.2, Grafana app
  13.2.0), created 2026-08-24.
- Workloads: prometheus (StatefulSet), alertmanager (StatefulSet), grafana,
  operator, kube-state-metrics, node-exporter (DaemonSet). All Running.
- Default PrometheusRule bundles installed (k8s.rules, etcd,
  kube-prometheus-general.rules, alertmanager.rules, …).
- **Storage: none persisted** — Prometheus DB and Grafana storage are
  `emptyDir` (no PVCs). This matches "start small" but means restarts lose
  history; the reference page's PVC guidance (50–100 GiB) is NOT yet applied.
- **Retention: unset** → chart default (10 days).
- Access: `prometheus-grafana` ClusterIP only (no Ingress/HTTPRoute yet).

```bash
# inspect release
sudo KUBECONFIG=/etc/rancher/rke2/rke2.yaml kubectl -n monitoring get pods
sudo KUBECONFIG=/etc/rancher/rke2/rke2.yaml kubectl -n monitoring get sts \
  prometheus-prometheus-kube-prometheus-prometheus -o json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print('VCT:', 'volumeClaimTemplates' in d['spec'])"
```

## Follow-ups (gaps vs the reference page)

1. Move the release under Argo CD (GitOps rule) or record the deliberate
   exception.
2. Add a PVC to Prometheus (+ decide retention, ref says 10–15 days).
3. Loki + Grafana Alloy (Part II stack selection) not deployed yet.
4. "Alert before things are full" rules for node disk — defaults only today.

## Commands

```bash
# provenance reconstruction
sudo KUBECONFIG=/etc/rancher/rke2/rke2.yaml kubectl -n monitoring get secrets | grep helm
# chart version decode from sh.helm.release.v1.prometheus.v1 (double-base64 + gzip)
```
