# dev Role

Example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tenant-developer
  namespace: dev-42admin
rules:
  - apiGroups: [""]
    resources:
      - pods
      - pods/log
      - pods/exec
      - pods/portforward
      - services
      - endpoints
      - configmaps
      - persistentvolumeclaims
      - events
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete

  - apiGroups: ["apps"]
    resources:
      - deployments
      - replicasets
      - statefulsets
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete

  - apiGroups: ["batch"]
    resources:
      - jobs
      - cronjobs
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete
```

Bind an identity group:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-42admin-developers
  namespace: dev-42admin
subjects:
  - kind: Group
    name: tenant-42admin
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: tenant-developer
  apiGroup: rbac.authorization.k8s.io
```

---
