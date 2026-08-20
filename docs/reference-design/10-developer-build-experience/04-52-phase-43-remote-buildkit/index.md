# Phase 43 — remote BuildKit

The developer runs a build command from alpha.

Buildx talks to BuildKit on build01.

Conceptually:

```text
~/projects/my-api on alpha
        |
        | build context
        v
remote BuildKit
        |
        | cached build
        v
Harbor
        |
        v
dev-jya0
```

Protect the BuildKit endpoint with:

```text
private network
TLS
client certificates
tenant-specific builder
```

Do not expose unauthenticated BuildKit TCP.

---
