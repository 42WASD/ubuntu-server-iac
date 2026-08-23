# HAMi validation

Do not describe HAMi as MIG.

Test:

```text
two pods
memory cap
compute cap
concurrent CUDA
one workload intentionally exceeds memory
one workload exits/crashes
node GPU health afterward
driver reset behavior
monitoring visibility
```

The acceptance criterion is not:

```text
both Pods started
```

It is:

```text
resource limit behaves as expected
failure behavior is understood
driver remains recoverable
other tenant's workload behavior is acceptable
```

If not:

```text
fall back to whole-GPU scheduling
```

---
