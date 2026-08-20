# Phase 30 — policy tests

Create intentionally-bad manifests under:

```text
kubernetes/policy-tests/
```

Examples:

```text
privileged-pod.yaml
hostpath-pod.yaml
hostnetwork-pod.yaml
no-resource-limits.yaml
nodeport-service.yaml
gpu-request-unapproved.yaml
```

The platform is not "secure because YAML exists."

It is secure when the forbidden test actually fails.

Example validation:

```bash
kubectl auth can-i create clusterrole --as <developer-identity>
kubectl auth can-i create pods -n dev-42wasd-admin --as <developer-identity>
kubectl auth can-i create pods -n prd-42wasd-admin --as <developer-identity>
```

Expected:

```text
cluster-wide: no
dev workload: yes
prod arbitrary write: no
```

---
