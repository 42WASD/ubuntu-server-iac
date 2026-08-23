---
order: 29
---

# Phase 29 — stage policy before enforcing it

Do not enable 25 deny policies in one commit.

Sequence:

```text
1. install Kyverno
2. add policies in Audit
3. inspect reports
4. fix platform/tenant workloads
5. change selected policies to Enforce
```

Minimum custom controls:

```text
deny privileged containers
deny hostPath
deny hostNetwork
deny hostPID
deny hostIPC
deny hostPort unless approved
require resource requests/limits
restrict NodePort
restrict LoadBalancer
restrict storage classes
restrict high PriorityClass
restrict GPU resources
require approved registry in prod
forbid :latest in prod
prefer immutable image digests in prod
```

Pod Security `restricted` already blocks many unsafe settings.

Kyverno adds organization-specific rules and clearer exceptions.

---
