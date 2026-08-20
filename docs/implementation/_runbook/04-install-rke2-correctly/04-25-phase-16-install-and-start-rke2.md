---
phase: 04-install-rke2-correctly/04-25-phase-16-install-and-start-rke2
---
# Phase 16 — install and start RKE2

**Intent:** install the pinned RKE2 release on `alpha`, enable and start the
`rke2-server` service, and verify the cluster reaches `Ready` with critical
components settled to `Running` / `Completed`.

## 16.1 The installer

The `rke2_server` role downloads the installer and runs it with the exact
pinned version from the environment (Phase 13):

```bash
curl -sfL https://get.rke2.io \
  | INSTALL_RKE2_VERSION='v1.36.3+rke2r1' sh -
```

As Ansible, this is expressed idempotently:

```yaml
# tasks/main.yml (Phase 16)
- name: Check if RKE2 is already installed
  ansible.builtin.stat:
    path: /usr/local/bin/rke2
  register: rke2_bin

- name: Install RKE2 if not already present
  when: not rke2_bin.stat.exists
  block:
    - name: Download the RKE2 installer script
      ansible.builtin.get_url:
        url: "{{ rke2_install_url }}"
        dest: "{{ rke2_install_script }}"
        mode: "0755"
        timeout: 60
    - name: Run the pinned RKE2 installer
      ansible.builtin.command:
        cmd: "INSTALL_RKE2_VERSION='{{ rke2_version }}' sh {{ rke2_install_script }}"
      environment:
        INSTALL_RKE2_TYPE: server
      register: rke2_install_result
      changed_when: true
    - name: Remove the installer script
      ansible.builtin.file:
        path: "{{ rke2_install_script }}"
        state: absent
```

- Idempotent: if `/usr/local/bin/rke2` already exists, install is skipped.
- `INSTALL_RKE2_TYPE=server` tells the installer we are a server, not an agent.
- The installer script is removed after use.

Then enable on boot and start:

```yaml
- name: Enable rke2-server on boot
  ansible.builtin.systemd:
    name: rke2-server
    enabled: true
    daemon_reload: true

- name: Start rke2-server
  ansible.builtin.systemd:
    name: rke2-server
    state: started
```

## 16.1.1 Manual verification commands (run after Ansible)

```bash
# Follow startup logs
sudo journalctl -u rke2-server -f

# In another shell: wait for alpha to be Ready
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get nodes -o wide

# Expect: alpha  Ready

# Then check all pods settle
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get pods -A
```

Expected critical components settle to `Running` / `Completed`, **not**
repeated `CrashLoopBackOff`, `ImagePullBackOff`, or `Pending`.

## 16.1.2 Live install results (executed on `alpha`, 2026-08-20)

Bootstrap config files were rendered from the role templates and placed on the
host (Phase 14 config.yaml, Phase 23.1 kubelet drop-in, Phase 15 Cilium
HelmChartConfig), then the pinned installer was run as root:

```bash
# Place bootstrap configs (Phase 14 / 23.1 / 15 prerequisites)
sudo mkdir -p /etc/rancher/rke2/kubelet.conf.d /var/lib/rancher/rke2/server/manifests
sudo cp /tmp/rke2-stage/config.yaml /etc/rancher/rke2/config.yaml
sudo cp /tmp/rke2-stage/kubelet.conf.d/00-platform.conf /etc/rancher/rke2/kubelet.conf.d/00-platform.conf
sudo cp /tmp/rke2-stage/rke2-cilium-config.yaml /var/lib/rancher/rke2/server/manifests/rke2-cilium-config.yaml

# Install the pinned release (must run as root)
curl -sfL https://get.rke2.io | sudo INSTALL_RKE2_VERSION='v1.36.3+rke2r1' sh -

# Enable + start
sudo systemctl enable rke2-server
sudo systemctl start rke2-server
```

Observed:

- Installer downloaded `v1.36.3+rke2r1`, verified checksums, unpacked to
  `/usr/local`.
- `rke2-server` became `active` and `enabled`.
- Node `alpha` reached `Ready` (control-plane,etcd, v1.36.3+rke2r1,
  containerd 2.3.3-k3s1) after a short bootstrap.
- Core addons all healthy: CoreDNS, metrics-server, Traefik daemonset, Hubble
  relay, Cilium agent daemonset, snapshot-controller.
- The 8 `helm-install-*` jobs reached `Completed`.

**Two bootstrap observations worth recording:**

1. **Traefik install CRD race (resolved automatically).** The first
   `helm-install-rke2-traefik` job briefly errored with
   `Required CRDs are missing...install the corresponding CRD chart first`.
   This is the standard RKE2 CRD bootstrap race; RKE2 retried and Traefik then
   came up `1/1`. No action was needed.

2. **Cilium operator scale-down (single-node optimization).** The bundled
   Cilium chart defaults the operator to **2 replicas** (HA). On a
   single-node cluster the second replica requests host ports that can bind
   only once per node, so it sat `Pending` forever. We set
   `operator.replicas: 1` in the Cilium HelmChartConfig
   (`rke2_cilium_operator_replicas: 1` in defaults). RKE2 reconciled the
   HelmChartConfig and scaled the operator down to 1; the node then had **all
   pods healthy** (13 Running, 8 Completed, zero Pending/error). When more
   nodes join, bump this back to 2.

## 16.2 What was implemented

- `rke2_server` defaults: `rke2_install_script: /tmp/rke2-install.sh`.
- `tasks/main.yml`: install (idempotent via `stat` guard), enable, and start
  `rke2-server`.
- This phase encodes the exact pinned version (Phase 13) and relies on the
  config written in Phases 14, 23.1, and 15 (config.yaml, kubelet drop-in,
  Cilium HelmChartConfig) to be consumed by the very first boot.

## 16.3 Commands run

Validated that `tasks/main.yml` and `defaults/main.yml` both parse as YAML
(Ansible not installed on `alpha`):

```bash
cd /home/jyao/ubuntu-server-iac
python3 - <<'PY'
import yaml
for f in [
  "infra/ansible/roles/rke2_server/tasks/main.yml",
  "infra/ansible/roles/rke2_server/defaults/main.yml",
]:
    with open(f) as fh:
        yaml.safe_load(fh)
    print(f, "OK")
PY
```

Both files parse cleanly. The installer command matches the pinned release
from Phase 13.