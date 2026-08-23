# install Harbor

Deploy Harbor through Argo CD into:

```text
registry
```

Use dedicated persistent storage.

Do not make Harbor your only copy of source code or Dockerfiles.

Images should always be rebuildable from:

```text
Git + build pipeline
```

Harbor policy:

```text
project: jya0
project: 42admin
project: platform

production tags immutable
retention rules
vulnerability scanning
registry GC
robot accounts for CI
human access per project
```

Keep registry access:

```text
LAN/Tailscale/private first
```

Do not expose it publicly merely because Cloudflare exists.

---
