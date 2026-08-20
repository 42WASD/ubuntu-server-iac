# Phase 53 — keep game workloads in Kubernetes for now

Do not solve individual game stacks yet.

Platform-level decision:

```text
games-42admin
```

gets:

```text
ResourceQuota
LimitRange
NetworkPolicy
persistent storage
monitoring
controlled external ports
```

That keeps game hosting inside the same infrastructure discipline.

Later we can choose per game:

```text
plain StatefulSet
Agones
operator
proxy layer
specialized controller
```

without changing the host platform.

---
