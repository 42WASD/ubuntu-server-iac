# The trust model

The platform has four different identities.

```text
HUMAN
  jyao, jya0, alice, bob, ...

PROJECT / TENANT
  tenant-jya0
  tenant-42wasd-admin

AUTOMATION
  Argo CD service accounts
  CI identities
  registry robots

MACHINE
  alpha
  build01
  future RKE2 workers
```

Do not collapse them.

Bad:

```text
five humans -> all SSH as 42admin
```

Good:

```text
alice -> Linux user alice -> member of tenant-42wasd-admin
bob   -> Linux user bob   -> member of tenant-42wasd-admin

Kubernetes group tenant-42wasd-admin
    -> dev-42admin permissions
    -> restricted prod visibility
```

Shared **project access** is useful.

Shared **human login identities** are not.

---
