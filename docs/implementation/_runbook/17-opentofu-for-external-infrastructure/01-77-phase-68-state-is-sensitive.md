---
phase: 17-opentofu-for-external-infrastructure/state-is-sensitive
---

# Phase 68 — state is sensitive

Acknowledgment note for Phase 68: OpenTofu state can contain sensitive values,
so it must never be committed. This phase's requirement is enforced by the
setup done in Phase 67.

## 68.1 What was enforced

Per Phase 68, the following are **never committed** to Git:

```text
terraform.tfstate
*.tfstate
```

Instead we use **encrypted remote state** — Cloudflare R2 (S3-compatible)
bucket `42base` — with backups. The dependency lock file is committed so
provider versions are reproducible.

This is encoded in `infra/tofu/.gitignore`:

```gitignore
# OpenTofu state is sensitive (reference-design Phase 68). Never commit.
*.tfstate
*.tfstate.*
.terraform/
# CRASH logs
crash.log
# Real secret files (gitignored)
terraform.tfvars
# But keep the example so the variable shape is documented:
!terraform.tfvars.example
```

## 68.2 Command used to verify state is not committed

Confirm the real secret files and state are ignored while the example files are
tracked:

```bash
git check-ignore -v infra/tofu/vps/terraform.tfvars        # -> ignored
git check-ignore -v infra/tofu/cloudflare/terraform.tfvars # -> ignored
git ls-files infra/tofu | grep tfvars                      # -> only *.example
```

Result: only `terraform.tfvars.example` files are committed; the real
`terraform.tfvars` and all state files stay local/remote-only.

## 68.3 What was acknowledged / used

- **Remote state:** Cloudflare R2 bucket `42base`, keys
  `vps/terraform.tfstate` and `cloudflare/terraform.tfstate`, encrypted at rest
  by R2.
- **Lockfile:** committed so provider versions are reproducible.
- **No state committed:** verified via the `git ls-files` / `git check-ignore`
  checks above.