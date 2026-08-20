---
phase: 04-install-rke2-correctly/02-23-1-kubelet-configuration
---
# Phase 14, sub-phase 23.1 — kubelet configuration

**Intent:** encode the kubelet configuration as infrastructure-as-code so that
the host reserves capacity for Linux + developers + Kubernetes system services,
and protects itself from disk/memory exhaustion — before RKE2 ever starts.

## 23.1.1 Why a kubelet config drop-in, not CLI flags

RKE2's preferred pattern for kubelet settings is config drop-ins rather than
piling everything onto `kubelet-arg` command-line flags. We point RKE2 at a
config directory with one entry in `config.yaml`:

```yaml
kubelet-arg:
  - "config-dir=/etc/rancher/rke2/kubelet.conf.d"
```

RKE2 then loads every file in `/etc/rancher/rke2/kubelet.conf.d/` as a kubelet
config fragment. This keeps the kubelet settings in a versioned, readable file
separate from the rest of the server config.

## 23.1.2 Values encoded (target: 64 CPU / 128 GiB physical)

These match the reference design's recommended initial target. They admit that
SSH users and the developer host exist outside Pod scheduling, and do **not**
attempt to schedule all 128 GiB of Pod requests on a machine where developers
also compile and test software directly.

<table>
<thead><tr><th>Field</th><th>Value</th><th>Why</th></tr></thead>
<tbody>
<tr><td><code>systemReserved.cpu</code></td><td><code>12</code></td><td>~12 CPU left outside normal Pod scheduling (Linux + developers)</td></tr>
<tr><td><code>systemReserved.memory</code></td><td><code>24Gi</code></td><td>~24 GiB for the host / developer workloads</td></tr>
<tr><td><code>systemReserved.ephemeral-storage</code></td><td><code>20Gi</code></td><td>host + developer scratch on the root disk</td></tr>
<tr><td><code>kubeReserved.cpu</code></td><td><code>2</code></td><td>Kubernetes system services (~2 CPU)</td></tr>
<tr><td><code>kubeReserved.memory</code></td><td><code>4Gi</code></td><td>Kubernetes system services (~4 GiB)</td></tr>
<tr><td><code>kubeReserved.ephemeral-storage</code></td><td><code>10Gi</code></td><td>Kubernetes system services disk</td></tr>
<tr><td><code>evictionHard.memory.available</code></td><td><code>8Gi</code></td><td>evict Pods before host OOM</td></tr>
<tr><td><code>evictionHard.nodefs.available</code></td><td><code>12%</code></td><td>protect the root filesystem</td></tr>
<tr><td><code>evictionHard.imagefs.available</code></td><td><code>15%</code></td><td>protect the image filesystem</td></tr>
<tr><td><code>evictionHard.nodefs.inodesFree</code></td><td><code>5%</code></td><td>protect against inode exhaustion</td></tr>
<tr><td><code>imageGCHighThresholdPercent</code></td><td><code>75</code></td><td>start aggressive image GC above 75%</td></tr>
<tr><td><code>imageGCLowThresholdPercent</code></td><td><code>60</code></td><td>stop image GC below 60%</td></tr>
<tr><td><code>seccompDefault</code></td><td><code>true</code></td><td>apply default seccomp profile to Pods that don't set one</td></tr>
</tbody>
</table>

> **Schema caveat:** the reference explicitly warns *"Do not blindly assume the
> exact kubelet config schema for your pinned Kubernetes minor."* We pin
> `apiVersion: kubelet.config.k8s.io/v1beta1` and `kind: KubeletConfiguration`.
> This is a versioned file; it must be validated against the installed kubelet
> and checked via kubelet logs after first boot (Phase 16).

## 23.1.3 What was implemented

- `rke2_server` role default vars for every field above (see
  `defaults/main.yml`, "kubelet configuration" section).
- `config.yaml.j2` now emits `kubelet-arg: config-dir={{ rke2_kubelet_conf_dir }}`.
- New template `templates/kubelet.conf.d/00-platform.conf.j2` renders the
  `KubeletConfiguration` drop-in.
- `tasks/main.yml` creates the kubelet config directory and renders the drop-in
  file (both root-owned, `0644`).

## 23.1.4 Commands run

Validated that both templates render to valid YAML (Ansible is not installed on
`alpha`, so we use plain `jinja2` + `yaml.safe_load`):

```bash
cd /home/jyao/ubuntu-server-iac
python3 - <<'PY'
from jinja2 import Environment, FileSystemLoader
import yaml
env = Environment(loader=FileSystemLoader("infra/ansible/roles/rke2_server/templates"))
v = {
  "rke2_server_name": "alpha",
  "rke2_cni": "cilium",
  "rke2_ingress_controller": "traefik",
  "rke2_disable_kube_proxy": True,
  "rke2_tls_sans": ["alpha.taild82ced.ts.net"],
  "rke2_write_kubeconfig_mode": "0640",
  "rke2_etcd_snapshot_schedule": "0 */6 * * *",
  "rke2_etcd_snapshot_retention": 12,
  "rke2_etcd_snapshot_compress": True,
  "rke2_node_labels": ["platform.example.com/role=core"],
  "rke2_config_dir": "/etc/rancher/rke2",
  "rke2_kubelet_conf_dir": "/etc/rancher/rke2/kubelet.conf.d",
  "rke2_kubelet_system_reserved": {"cpu": "12", "memory": "24Gi", "ephemeral-storage": "20Gi"},
  "rke2_kubelet_kube_reserved": {"cpu": "2", "memory": "4Gi", "ephemeral-storage": "10Gi"},
  "rke2_kubelet_eviction_hard": {"memory.available": "8Gi", "nodefs.available": "12%",
                                  "imagefs.available": "15%", "nodefs.inodesFree": "5%"},
  "rke2_kubelet_image_gc_high_threshold": 75,
  "rke2_kubelet_image_gc_low_threshold": 60,
  "rke2_kubelet_seccomp_default": True,
}
cfg = env.get_template("config.yaml.j2").render(**v)
yaml.safe_load(cfg)
print("config.yaml OK")
kb = env.get_template("kubelet.conf.d/00-platform.conf.j2").render(**v)
yaml.safe_load(kb)
print("kubelet drop-in OK")
PY
```

Both templates render to valid YAML. The kubelet drop-in resolves to a
`KubeletConfiguration` with the table above.