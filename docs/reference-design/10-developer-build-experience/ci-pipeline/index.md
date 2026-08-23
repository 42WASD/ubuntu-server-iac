---
order: 45
---

# Phase 45 — CI pipeline

Interactive dev and CI are different.

Interactive:

```text
developer
-> skaffold dev
-> tenant builder
-> dev namespace
```

CI:

```text
Git push / PR
-> CI runner
-> lint
-> unit test
-> build
-> image scan
-> integration test
-> push immutable image
```

Production:

```text
merge/promotion
-> update GitOps image digest/tag
-> Argo CD
-> prod namespace
```

Do not give CI a permanent cluster-admin kubeconfig.

CI should mostly produce:

```text
test result
image
Git commit / promotion PR
```

Argo performs deployment.

---
