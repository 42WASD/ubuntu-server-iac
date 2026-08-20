# Phase 68 — state is sensitive

OpenTofu state can contain sensitive values.

Do not commit:

```text
terraform.tfstate
*.tfstate
```

Use:

```text
encrypted remote state
or
encrypted/local protected state for early bootstrap
```

with backups.

Commit the dependency lock file when appropriate so provider versions are reproducible.

---
