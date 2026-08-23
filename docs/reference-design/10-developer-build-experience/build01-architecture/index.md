---
order: 41
---

# Phase 41 — build01 architecture

Build node:

```text
build01

LXD
├── builder-jya0
├── builder-42admin
└── CI VM
```

Trusted internal builders can use unprivileged LXD system containers.

Untrusted/public PR code should use a disposable VM or hosted runner.

The builder machine owns:

```text
build CPU
build RAM
container layer extraction
image cache
build logs
temporary build files
```

Alpha does not.

---
