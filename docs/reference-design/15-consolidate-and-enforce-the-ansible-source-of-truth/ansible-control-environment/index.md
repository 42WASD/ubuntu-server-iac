# Ansible control environment

You should already have been codifying each completed phase into Ansible. This section makes the final structure explicit and prepares the same repository to configure `build01` and future RKE2 workers.

Run Ansible from your admin laptop or a dedicated control environment.

Create venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install ansible-core
```

Create:

```yaml
# ansible/requirements.yml
collections:
  - name: ansible.posix
  - name: community.general
  - name: kubernetes.core
```

Install:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

Pin your own tested collection versions later.

---
