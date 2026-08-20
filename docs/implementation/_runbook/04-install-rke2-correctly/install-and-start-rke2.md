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