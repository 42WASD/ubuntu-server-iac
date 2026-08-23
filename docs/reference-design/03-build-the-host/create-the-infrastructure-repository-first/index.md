# create the infrastructure repository first

Do this from your admin workstation or from `jyao`.

Recommended repository:

```text
infra/
├── README.md
├── Makefile
├── docs/
│   ├── architecture.md
│   ├── disaster-recovery.md
│   └── upgrade-runbook.md
├── inventory/
│   ├── production.yml
│   ├── group_vars/
│   │   ├── all.yml
│   │   ├── rke2.yml
│   │   └── builders.yml
│   └── host_vars/
│       ├── alpha.yml
│       └── build01.yml
├── autoinstall/
│   ├── alpha.yaml
│   └── build01.yaml
├── ansible/
│   ├── ansible.cfg
│   ├── requirements.yml
│   ├── site.yml
│   └── roles/
│       ├── base/
│       ├── users/
│       ├── storage/
│       ├── ssh/
│       ├── tailscale/
│       ├── firewall/
│       ├── developer_limits/
│       ├── nvidia_host/
│       ├── rke2_server/
│       ├── rke2_agent/
│       ├── build_client/
│       └── build_node/
├── kubernetes/
│   ├── bootstrap/
│   │   └── argocd/
│   ├── platform/
│   │   ├── namespaces/
│   │   ├── cilium/
│   │   ├── traefik/
│   │   ├── policy/
│   │   ├── storage/
│   │   ├── monitoring/
│   │   ├── registry/
│   │   ├── cloudflare/
│   │   └── gpu/
│   └── tenants/
│       ├── jya0/
│       │   ├── dev/
│       │   ├── prod/
│       │   ├── ml/
│       │   └── gpu/
│       └── 42admin/
│           ├── dev/
│           ├── prod/
│           └── games/
├── tofu/
│   ├── cloudflare/
│   └── relay/
└── developer/
    ├── templates/
    ├── skaffold/
    └── remote-build/
```

Create it:

```bash
mkdir -p infra/{docs,inventory/{group_vars,host_vars},autoinstall,ansible/roles,kubernetes/{bootstrap/argocd,platform,tenants},tofu,developer}
cd infra
git init
```

Create a minimal Ansible entry point now:

```yaml
# ansible/site.yml

- name: Configure all Linux platform nodes
  hosts: all
  become: true
  roles:
    - base
    - users
    - tailscale
    - firewall
    - developer_limits

- name: Configure RKE2 servers
  hosts: rke2_servers
  become: true
  roles:
    - storage
    - nvidia_host
    - rke2_server

- name: Configure build nodes
  hosts: build_nodes
  become: true
  roles:
    - build_node
```

During early phases, roles that are not implemented yet can be commented out. The point is to establish the ownership model before configuration spreads across ad-hoc scripts.

Create a small `Makefile` interface:

```make
INVENTORY ?= inventory/production.yml

.PHONY: check ansible bootstrap verify

check:
	ansible-inventory -i $(INVENTORY) --graph
	ansible all -i $(INVENTORY) -m ping

ansible:
	ansible-playbook -i $(INVENTORY) ansible/site.yml

bootstrap:
	$(MAKE) check
	$(MAKE) ansible

verify:
	ansible rke2_servers -i $(INVENTORY) -a 'systemctl --failed'
```

The long-term goal is that an administrator remembers:

```bash
make check
make bootstrap
make verify
```

instead of remembering 80 one-off commands.

Create `.gitignore` immediately:

```gitignore
# secrets
*.key
*.pem
*.p12
*.pfx
.env
.env.*
!*.example

# Ansible
*.retry
.vault-password
ansible/.venv/

# OpenTofu / Terraform
**/.terraform/
**/.tofu/
*.tfstate
*.tfstate.*
*.tfplan
crash.log

# kubeconfig
kubeconfig
*.kubeconfig

# generated secrets
secrets.generated/
```

## Checkpoint 0

```bash
git status
```

Expected:

```text
clean repository after your initial commit
```

Do not continue until the repository exists.

---
