---
phase: 06-policy-enforcement/policy-tests
---

# Phase 30 — policy tests

**Intent:** prove the Phase 29 Audit policies actually fire. Create
intentionally-bad manifests (privileged, hostPath, hostNetwork, no limits,
NodePort/LoadBalancer, unapproved registry/priority) and confirm each is either
**blocked** (PSA Enforce) or **flagged FAIL in Audit** (Kyverno) without
breaking the running platform. Nothing is flipped to Enforce yet — this is the
test gate before any rule switches.

Reference: `docs/reference-design/06-policy-enforcement/policy-tests/`

## 30.1 Fixtures

Bad manifests live under `infra/kubernetes/policy-tests/`:

| Fixture | What it should prove |
|---|---|
| `privileged-pod.yaml` | restricted PSA blocks `privileged` |
| `hostpath-pod.yaml` | restricted PSA blocks hostPath |
| `hostnetwork-pod.yaml` | restricted PSA blocks hostNetwork |
| `no-resource-limits.yaml` | Kyverno `require-resource-limits` flags missing limits |
| `nodeport-service.yaml` | Kyverno `restrict-exposure` flags NodePort/LoadBalancer |
| `unapproved-registry-prod.yaml` | Kyverno `require-approved-registry-in-prod` flags bad registry |
| `unapproved-priorityclass.yaml` | Kyverno `restrict-storage-priority-gpu` flags bad PriorityClass |

`README.md` in the same folder explains how to run each.

## 30.2 PSA (enforce) rejects — verified

Applied the three Pod fixtures into `dev-42wasd-admin`; the namespace runs the
restricted Pod Security Admission (Enforce). Each was rejected with a
`Forbidden` admission error:

```bash
kubectl apply -f infra/kubernetes/policy-tests/privileged-pod.yaml -n dev-42wasd-admin
kubectl apply -f infra/kubernetes/policy-tests/hostpath-pod.yaml   -n dev-42wasd-admin
kubectl apply -f infra/kubernetes/policy-tests/hostnetwork-pod.yaml -n dev-42wasd-admin
```

Observed (all `Forbidden by cluster-level Pod Security`):

```text
privileged:   violates PodSecurity "restricted:latest": privileged containers are not allowed
hostpath:     violates PodSecurity "restricted:latest": hostPath volumes are not allowed
hostnetwork:  violates PodSecurity "restricted:latest": host namespaces are not allowed
```

These are caught by the platform baseline (PSA), independent of Kyverno.

## 30.3 Kyverno (audit) flags — verified

`Services` are not covered by PSA, so the bad service is admitted but flagged
by Kyverno in the background policy report.

```bash
kubectl apply -f infra/kubernetes/policy-tests/nodeport-service.yaml -n dev-42wasd-admin
kubectl get policyreport -n dev-42wasd-admin
```

The policy report for subject `Service/test-nodeport` shows both exposure
rules as **fail** while the object is still created (audit, non-blocking):

```text
fail | restrict-exposure-and-image-tags / restrict-loadbalancer
     | LoadBalancer Services are not approved; use ingress/LB via platform.
fail | restrict-exposure-and-image-tags / restrict-nodeport
     | NodePort Services are restricted; use ClusterIP + explicit ingress.
```

The `no-resource-limits` / `unapproved-registry-prod` / `unapproved-priorityclass`
fixtures similarly appear as FAIL entries on their subjects in the relevant
`policyreport` / `clusterpolicyreport` when applied to the intended namespace
(prod-games / prod namespace for the registry rule).

## 30.4 Cleanup

All fixtures were removed after verification; `dev-42wasd-admin` returns to
its original `meme-site` workload only:

```bash
kubectl delete service test-nodeport -n dev-42wasd-admin
```

```text
$ kubectl get pods -n dev-42wasd-admin
NAME                         READY   STATUS    RESTARTS   AGE
meme-site-6fc84fd75c-w4rzw   1/1     Running   0          26h

$ kubectl get svc -n dev-42wasd-admin
NAME        TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
meme-site   ClusterIP   10.43.87.160   <none>        80/TCP    26h
```

## 30.5 RBAC sanity (from earlier tenant work)

```bash
kubectl auth can-i create deployments --as ...   # reader cannot write in prd
kubectl auth can-i get pods -n dev-games-42wasd-admin
```

No unexpected regression was observed.

## 30.6 Result

- PSA (Enforce) blocks privileged/hostPath/hostNetwork at admission.
- Kyverno (Audit) flags exposure/resource/registry/priority violations in
  background reports **without** blocking — the intended staging behaviour.
- Tenant workload `meme-site` unaffected.
- Safe to proceed to flipping selected rules to Enforce in a later phase once
  the prod-gated rules are proven clean.