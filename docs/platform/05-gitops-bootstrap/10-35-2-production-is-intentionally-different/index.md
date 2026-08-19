# production is intentionally different

In prod, developers should mostly receive:

```text
get
list
watch
logs
events
possibly port-forward
```

Application **writes** come from Argo CD.

Why?

Because someone who can create arbitrary Pods in a namespace can often mount Secrets from that namespace even if RBAC denies direct `get secret`.

So:

```text
"cannot read Secret"
+
"can create arbitrary prod Pod"
```

is not a meaningful secret boundary.

---
