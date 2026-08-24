---
phase: 04-install-rke2-correctly/rke2-configuration
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
<tr><td><code>tls-san</code></td><td><code>alpha.taild82ced.ts.net</code></td><td>API serving cert valid through the stable Tailscale MagicDNS name</td></tr>
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

> **Why the MagicDNS name, not the IP:** the raw `100.x` Tailscale IP can be
> reallocated, but the MagicDNS hostname (`alpha.taild82ced.ts.net`) stays tied
> to the node. Using it in `tls-san` keeps the serving cert valid across Tailscale
> address changes. The raw IP is retained in host_vars as a fallback.

### 14.1.1 Token lifecycle (decided here)

Because `config.yaml` does **not** set a `token:`, RKE2 will **auto-generate a
random cluster token on first boot** and store it at:

```text
/var/lib/rancher/rke2/server/token
```

This token is used for both:
- joining new nodes (agents / additional servers), and
- encrypting cluster bootstrap data in the datastore (recovery material).

Implications we accept deliberately:

- **Never commit it to Git.** This is the reference design's rule and the reason
  we did not put a `token:` in the config.
- It is **recovery material**: when backups run (Phase 56/57) the token file
  must be captured off-host.
- When the first agent/server is added later, join using the existing token
  (e.g. `INSTALL_RKE2_AGENT_TOKEN="$(cat /var/lib/rancher/rke2/server/token)"`),
  or pre-generate a strong token and store it in **Ansible Vault** (gitignored
  `.vault-password` + encrypted `group_vars/rke2.yml`), never plaintext.

Single-node today, so no join flow exists yet — the generated token is simply
recorded as recovery material.

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

## 14.4 Day-2 recovery: RKE2 crash-loop from malformed config.yaml (2026-08-24)

**Symptom:** `kubectl` could not reach the API server (`connection refused` on
`alpha.taild82ced.ts.net:6443`); `rke2-server.service` was crash-looping
(restart counter ~1850) with:

```text
rke2[NNNN]: level=fatal msg="yaml: line 18: block sequence entries are not
allowed in this context"
```

**Root cause:** the live `/etc/rancher/rke2/config.yaml` on the host had YAML
sequence items glued onto the same line as their key:

```yaml
tls-san:  - "alpha.taild82ced.ts.net"      # INVALID — dash on same line as key
node-label:  - "..." - "..." - "..."       # INVALID
```

The committed Jinja template (`config.yaml.j2`) renders correctly; the live
file was stale (written from an older/buggy render and never re-applied). A
malformed `config.yaml` is fatal to `rke2 server` before etcd/apiserver start,
so **every** PVC/PV/CAS operation hangs while the cluster is down — the
"slow PVC release" symptom is really the cluster being down.

**Fix (recover to match the committed template):**

```bash
# Render the committed template with the real values to a temp file, validate,
# then install and restart.
python3 -c "import yaml; yaml.safe_load(open('/tmp/config_fixed.yaml')); print('VALID')"
sudo cp /tmp/config_fixed.yaml /etc/rancher/rke2/config.yaml
sudo systemctl restart rke2-server
systemctl is-active rke2-server   # -> active
kubectl get nodes                  # -> alpha Ready
```

Verify the live file matches what the template would render, and diff the two:

```bash
diff <(grep -vE '^\s*#|^\s*$' /tmp/config_fixed.yaml) \
     <(grep -vE '^\s*#|^\s*$' /etc/rancher/rke2/config.yaml)  # -> IDENTICAL
```

**Lesson:** the Ansible role is the single source of truth for
`config.yaml`. If the file on disk ever differs from the rendered template,
re-run the role (or re-apply the rendered file) rather than hand-editing —
hand edits that break YAML silently take the whole cluster down.