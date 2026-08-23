# use Autoinstall for future clean rebuilds

Do **not** rush to reinstall the current working server merely to use Autoinstall.

First get the platform working manually + Ansible.

Then capture the known-good OS bootstrap.

Ubuntu Autoinstall can define:

```text
identity
SSH key
packages
storage layout
network
late commands
```

Use the top-level:

```yaml
#cloud-config
autoinstall:
  version: 1
```

---
