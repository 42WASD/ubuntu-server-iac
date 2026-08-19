# Initial quota reference

Use these as starting ceilings, then tune from monitoring.

| Namespace | CPU request | CPU limit | RAM request | RAM limit | Ephemeral | PVC | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|
| `dev-jya0` | 4 | 8 | 8Gi | 16Gi | 40Gi | 150Gi | 0 |
| `prod-jya0` | 8 | 12 | 16Gi | 24Gi | 60Gi | 300Gi | approved |
| `ml-jya0` | 6 | 12 | 12Gi | 24Gi | 100Gi | 500Gi | 0 initially |
| `gpu-jya0` | 8 | 16 | 16Gi | 32Gi | 120Gi | 500Gi | shared approved |
| `dev-42admin` | 4 | 8 | 8Gi | 16Gi | 40Gi | 100Gi | 0 |
| `prod-42admin` | 6 | 12 | 12Gi | 24Gi | 60Gi | 200Gi | 0 |
| `games-42admin` | tune after games | tune | tune | tune | tune | game-world needs | 0 |
| future dev | 2 | 4 | 4Gi | 8Gi | 20Gi | 50Gi | 0 |
| future prod | 4 | 8 | 8Gi | 16Gi | 40Gi | 100Gi | 0 |

Remember:

```text
sum of quotas may exceed physical capacity
```

but:

```text
sum of actual scheduled requests cannot
```

---
