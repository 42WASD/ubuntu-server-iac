# install Kyverno through Argo CD

Use a pinned Helm chart version.

Kyverno belongs in its own namespace:

```text
kyverno
```

Do not put it in `kube-system`.

Single-node note:

```text
3 replicas on one physical node
!=
real high availability
```

Start with a sensible single replica per controller, then increase only if workload volume requires it.

---
