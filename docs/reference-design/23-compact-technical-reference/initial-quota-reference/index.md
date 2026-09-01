# Initial quota reference

Use these as starting ceilings, then tune from monitoring.

| Namespace | CPU request | CPU limit | RAM request | RAM limit | Ephemeral | PVC | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|
| `mlops` | 8 | 16 | 16Gi | 32Gi | 120Gi | 500Gi | shared approved |
| `dev-42wasd-admin` | 4 | 8 | 8Gi | 16Gi | 40Gi | 100Gi | 0 |
| `prd-42wasd-admin` | 6 | 12 | 12Gi | 24Gi | 60Gi | 200Gi | 0 |
| `prd-games-42wasd-admin` | tune after games | tune | tune | tune | tune | game-world needs | 0 |
| `dev-games-42wasd-admin` | low (staging) | low | low | low | low | one game copy | 0 |
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
