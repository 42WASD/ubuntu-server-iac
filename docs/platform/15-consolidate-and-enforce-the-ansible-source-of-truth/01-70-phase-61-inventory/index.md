# Phase 61 — inventory

Example:

```yaml
# inventory/production.yml

all:
  children:

    rke2_servers:
      hosts:
        alpha:
          ansible_host: "<ALPHA_TAILSCALE_IP>"

    rke2_agents:
      hosts: {}

    build_nodes:
      hosts:
        build01:
          ansible_host: "<BUILD01_TAILSCALE_IP>"
```

Host vars:

```yaml
# inventory/host_vars/alpha.yml

node_role: rke2_server
rke2_node_name: alpha

developer_limits:
  jya0:
    cpu_quota_percent: 800
    memory_high: 16G
    memory_max: 24G

storage:
  k8s_fast_vg: vg_k8s_nvme
  k8s_bulk_vg: vg_k8s_hdd
```

---
