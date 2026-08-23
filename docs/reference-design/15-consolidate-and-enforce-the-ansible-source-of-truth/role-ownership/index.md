---
order: 62
---

# Phase 62 — role ownership

`base`:

```text
packages
time
journald
AppArmor checks
sysctl
SMART
```

`users`:

```text
users
groups
SSH authorized keys
sudo
```

`tailscale`:

```text
package
service
join configuration
```

`firewall`:

```text
host_filter nftables table only
```

`developer_limits`:

```text
systemd user slice drop-ins
quota configuration
```

`storage`:

```text
mountpoints
LVM verification
safe creation only when device mappings are explicit
```

`nvidia_host`:

```text
driver installation/verification
```

`rke2_server`:

```text
RKE2 version
config.yaml
Cilium HelmChartConfig
service enable/start
health checks
```

`build_client`:

```text
Skaffold
Buildx/client wrapper
developer config
```

---
