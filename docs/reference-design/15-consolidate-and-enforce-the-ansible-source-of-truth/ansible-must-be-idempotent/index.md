# Ansible must be idempotent

The test:

```bash
ansible-playbook -i inventory/production.yml ansible/site.yml
```

Run it.

Then run it again.

Second run should be mostly:

```text
changed=0
```

not:

```text
recreates users
rewrites disks
regenerates secrets
restarts RKE2 every time
```

Destructive storage operations should require an explicit opt-in variable such as:

```yaml
allow_storage_initialization: false
```

and should assert exact device serial/path information before execution.

---
