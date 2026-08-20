# infra

Infrastructure-as-Code repository for the RKE2 Kubernetes platform running on Ubuntu.

This repository is the source of truth for building and operating the platform
hosts. It is created and owned up front, before any configuration spreads
across ad-hoc scripts.

## Layout

- `ansible/` — configuration management for the platform hosts (the source of truth)
- `inventory/` — Ansible inventory (production, group_vars, host_vars)
- `autoinstall/` — Ubuntu autoinstall configurations for fresh host installs
- `kubernetes/` — manifests applied to the cluster (bootstrap, platform, tenants)
- `tofu/` — OpenTofu/Terraform for external infrastructure (Cloudflare, relay)
- `developer/` — developer build experience (templates, skaffold, remote-build)

## Day-to-day operations

The long-term goal is that an administrator remembers three commands:

```bash
make check     # validate inventory + connectivity
make bootstrap # run the full site playbook
make verify    # confirm the platform is healthy
```

instead of remembering 80 one-off commands.

## Quick reference

- `make check` — validate inventory graph and ping all hosts
- `make ansible` — run `ansible/site.yml`
- `make bootstrap` — `check` then `ansible`
- `make verify` — check for failed systemd units on RKE2 servers

See `docs/architecture.md`, `docs/disaster-recovery.md`, and
`docs/upgrade-runbook.md` for design and operational detail.