# Phase 25 — default-deny NetworkPolicy

Put this in every tenant namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: dev-42wasd-admin
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

Then allow DNS.

Example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-cluster-dns
  namespace: dev-42wasd-admin
spec:
  podSelector: {}
  policyTypes:
    - Egress

  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system

      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

Then add only the actual flows the application needs.

Example mental model:

```text
public frontend
    -> API
        -> PostgreSQL

random dev Pod
    -X-> PostgreSQL

compromised API
    -X-> home router / NAS / Tailscale management network
```

Cilium-specific egress controls can later enforce home-LAN exclusions more precisely.

---
