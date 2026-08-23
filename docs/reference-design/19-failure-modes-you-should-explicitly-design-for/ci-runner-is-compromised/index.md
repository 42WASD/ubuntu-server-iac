---
order: 3
---

# CI runner is compromised

Expected:

```text
runner can build/push its authorized project
runner cannot SSH root to alpha
runner does not hold cluster-admin kubeconfig
prod deploy still comes through GitOps
```

For untrusted/public PRs:

```text
disposable VM / hosted runner
```

not a long-lived trusted builder.

---
