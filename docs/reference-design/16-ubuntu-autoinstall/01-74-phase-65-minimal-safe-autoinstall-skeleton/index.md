# Phase 65 — minimal safe autoinstall skeleton

Example:

```yaml
#cloud-config

autoinstall:
  version: 1

  locale: en_US.UTF-8
  keyboard:
    layout: us

  identity:
    hostname: alpha
    username: jyao
    password: "<CRYPTED_INSTALLER_PASSWORD>"

  ssh:
    install-server: true
    allow-pw: false
    authorized-keys:
      - "<JYAO_SSH_PUBLIC_KEY>"

  storage:
    layout:
      name: lvm

  packages:
    - curl
    - git
    - python3
    - python3-venv
    - lvm2
    - xfsprogs
    - smartmontools
    - nvme-cli
```

This is intentionally **not** the final destructive disk design.

Autoinstall storage should eventually match disks by stable identifiers such as serial/model properties.

Do not use:

```yaml
match: {}
```

on a multi-disk production machine and assume it chooses the right disk.

---
