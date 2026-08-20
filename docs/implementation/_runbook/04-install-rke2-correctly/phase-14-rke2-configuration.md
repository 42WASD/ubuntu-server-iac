---
phase: 04-install-rke2-correctly/01-23-phase-14-rke2-configuration
---
# Phase 14 — RKE2 configuration

**Intent:** define the RKE2 server configuration file (`/etc/rancher/rke2/config.yaml`)
as infrastructure-as-code before we ever install RKE2, so the install in
Phase 16 bootstraps with the right networking, ingress, certificates, etcd
backups, and node labels from day one.

## 14.1 Design decisions encoded in config.yaml

<table>
<thead><tr><th>Field</th><th>Value</th><th>Why</th></tr></thead>
<tbody>
<tr><td><code>node-name</code></td><td><code>alpha</code></td><td>stable, short, matches inventory hostname</td></tr>
<tr><td><code>cni</code></td><td><code>cilium</code></td><td>bundled CNI; needed for kube-proxy replacement</td></tr>
<tr><td><code>ingress-controller</code></td><td><code>traefik</code></td><td>default for new v1.36 clusters (ingress-nginx retired upstream)</td></tr>
<tr><td><code>disable-kube-proxy</code></td><td><code>true</code></td><td>use Cilium's kube-proxy replacement (kube-proxy disabled)</td></tr>
<tr><td><code>tls-san</code></td><td><code>100.112.202.47</code></td><td>API serving cert valid through the Tailscale management IP</td></tr>
<tr><td><code>write-kubeconfig-mode</code></td><td><code>0640</code></td><td>admin kubeconfig readable by root/platform-admin group only</td></tr>
<tr><td><code>etcd-snapshot-schedule-cron</code></td><td><code>0 */6 * * *</code></td><td>etcd snapshot every 6 hours</td></tr>
<tr><td><code>etcd-snapshot-retention</code></td><td><code>12</code></td><td>keep 12 snapshots</td></tr>
<tr><td><code>etcd-snapshot-compress</code></td><td><code>true</code></td><td>gzip snapshots</td></tr>
</tbody>
</table>

Node labels (for future scheduling):

```text
platform.example.com/role=core
platform.example.com/storage-nvme=true
platform.example.com/storage-hdd=true
platform.example.com/gpu=true
```

**Security boundary:** the cluster token is deliberately **NOT** in this file or in
Git. It is generated at install time and stored only on the host.

## 14.2 Files on the host

```bash
sudo mkdir -p /etc/rancher/rke2
sudoedit /etc/rancher/rke2/config.yaml
```

## 14.3 Validation

The rendered config.yaml is validated as correct YAML and the values match the
table above (verified by rendering the Jinja template with the expected
variable values). Actual RKE2 install/boot validation happens in Phase 16.

---

**Infra encoding:**
- `infra/ansible/roles/rke2_server/defaults/main.yml` — all `rke2_*` config
  variables (cni, ingress, tls-san, etcd snapshot, node labels, config path/perms).
- `infra/ansible/roles/rke2_server/templates/config.yaml.j2` — renders the config file.
- `infra/ansible/roles/rke2_server/tasks/main.yml` — creates the dir + writes the file.
- The token is never committed; it is provided at install time.