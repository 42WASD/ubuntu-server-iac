---
order: 42
---

# Phase 42 — BuildKit cache policy

BuildKit supports its own garbage collection.

Example conceptual `buildkitd.toml`:

```toml
[worker.oci]
  enabled = true
  rootless = true
  max-parallelism = 8

  gc = true
  reservedSpace = "40GB"
  maxUsedSpace = "200GB"
  minFreeSpace = "100GB"
```

Then add version-appropriate GC policies for stale cache age if needed.

Meaning:

```text
keep useful cache
but never let cache consume the whole builder disk
```

Build cache belongs on build01.

Harbor retention belongs in Harbor.

Developer home quota belongs on alpha.

Three different lifecycle systems.

---
