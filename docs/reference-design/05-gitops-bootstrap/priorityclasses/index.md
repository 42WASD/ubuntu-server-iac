---
order: 22
---

# Phase 22 — PriorityClasses

Create only a small set.

Example:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: platform-critical-custom
value: 100000
globalDefault: false
description: "Critical platform workloads managed by platform admins."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: prod-high
value: 20000
globalDefault: false
description: "Tenant production workloads."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: dev-normal
value: 1000
globalDefault: false
description: "Normal development workloads."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: build-low
value: -1000
globalDefault: false
description: "Build / disposable workloads that should yield first."
```

Avoid giant priority inflation.

If every developer can declare `platform-critical`, priorities are meaningless.

Kyverno/RBAC should restrict who may use elevated classes.

---
