# Phase 3 — hostname, DNS, and local identity

Set hostname:

```bash
sudo hostnamectl set-hostname alpha
```

Verify:

```bash
hostnamectl
hostname -f
```

Keep `/etc/hosts` sane:

```text
127.0.0.1 localhost
127.0.1.1 alpha
```

Do not invent a fake public FQDN before the domain exists.

---
