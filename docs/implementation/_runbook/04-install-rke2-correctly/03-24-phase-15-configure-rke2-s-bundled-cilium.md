---
phase: 04-install-rke2-correctly/configure-rke2-s-bundled-cilium
---

# Phase 15 — configure RKE2's bundled Cilium

**Intent:** configure RKE2's **packaged** Cilium chart via a `HelmChartConfig`
so that kube-proxy replacement, API-server reachability, and the Hubble
observability path are correct from the very first cluster boot. We do **not**
install a second upstream Cilium Helm release on top of the bundled chart.

## 15.1 The HelmChartConfig

RKE2 watches the directory `/var/lib/rancher/rke2/server/manifests/` for
`HelmChartConfig` resources and applies them to the bundled Cilium chart. The
file rendered by the `rke2_server` role is
`rke2-cilium-config.yaml`:

```yaml
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: rke2-cilium
  namespace: kube-system
spec:
  valuesContent: |-
    kubeProxyReplacement: true

    k8sServiceHost: localhost
    k8sServicePort: "6443"

    operator:
      replicas: 1

    hubble:
      enabled: true
      relay:
        enabled: true
      ui:
        enabled: false
```

> **`operator.replicas: 1` note:** the bundled Cilium chart defaults the
> operator to **2 replicas** (HA). On a single-node cluster the second replica
> requests host ports that bind only once per node, so it sits `Pending`
> forever. We set it to **1** (`rke2_cilium_operator_replicas: 1`) until more
> nodes join; bump back to 2 when they do.

## 15.2 Why these values

<table>
<thead><tr><th>Field</th><th>Value</th><th>Why</th></tr></thead>
<tbody>
<tr><td><code>kubeProxyReplacement</code></td><td><code>true</code></td><td>use Cilium's eBPF kube-proxy replacement; matches <code>disable-kube-proxy: true</code> in <code>config.yaml</code></td></tr>
<tr><td><code>k8sServiceHost</code></td><td><code>localhost</code></td><td>API server reachable from Cilium agents on this node</td></tr>
<tr><td><code>k8sServicePort</code></td><td><code>6443</code></td><td>standard RKE2 API server port</td></tr>
<tr><td><code>operator.replicas</code></td><td><code>1</code></td><td>single-node cluster; the 2nd HA replica can't bind host ports (see note)</td></tr>
<tr><td><code>hubble.enabled</code></td><td><code>true</code></td><td>start the observability / flow metric path</td></tr>
<tr><td><code>hubble.relay.enabled</code></td><td><code>true</code></td><td>aggregate Hubble flows for the metrics backend</td></tr>
<tr><td><code>hubble.ui.enabled</code></td><td><code>false</code></td><td>do NOT expose an admin web UI yet (no private-access policy exists)</td></tr>
</tbody>
</table>

> **Why Hubble UI is disabled initially:** stand up the metrics/observability
> backend first; expose an admin web UI only after a private-access policy
> exists. We avoid creating another web admin surface before that policy is in
> place.

## 15.3 What was implemented

- `rke2_server` role defaults for every Cilium value (see `defaults/main.yml`,
  "Cilium configuration" section).
- New template `templates/rke2-cilium-config.yaml.j2` renders the
  `HelmChartConfig`.
- `tasks/main.yml` creates the RKE2 server manifests directory
  (`/var/lib/rancher/rke2/server/manifests/`) and renders the Cilium config
  file (root-owned, `0644`).

## 15.4 Commands run

Validated the template renders to valid YAML (Ansible is not installed on
`alpha`, so we use plain `jinja2` + `yaml.safe_load`):

```bash
cd /home/jyao/ubuntu-server-iac
python3 - <<'PY'
from jinja2 import Environment, FileSystemLoader
import yaml
env = Environment(loader=FileSystemLoader("infra/ansible/roles/rke2_server/templates"))
v = {
  "rke2_cilium_kube_proxy_replacement": True,
  "rke2_cilium_k8s_service_host": "localhost",
  "rke2_cilium_k8s_service_port": "6443",
  "rke2_cilium_hubble_enabled": True,
  "rke2_cilium_hubble_relay_enabled": True,
  "rke2_cilium_hubble_ui_enabled": False,
}
out = env.get_template("rke2-cilium-config.yaml.j2").render(**v)
yaml.safe_load(out)
print("OK cilium parses")
PY
```

The rendered `HelmChartConfig` parses as valid YAML and matches the reference
design's recommended Cilium configuration.