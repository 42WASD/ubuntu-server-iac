# Phase 67 — what OpenTofu should own

Use OpenTofu for resources created through external APIs:

```text
Cloudflare DNS records
Cloudflare tunnel/access configuration where provider support fits
OCI relay VM
OCI VCN/security rules
AWS/Azure relay alternative
public IP resources
```

Do not use OpenTofu to manage:

```text
apt packages on alpha
/etc/ssh/sshd_config
RKE2 systemd service
```

That is Ansible's job.

---
