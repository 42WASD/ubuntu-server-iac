# default-deny NetworkPolicy

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

Then allow DNS:

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

## Every tenant must also reach the kube-apiserver

A pod selected by an egress `default-deny` policy has **all** egress blocked
except what is explicitly allowed. Any workload that calls the Kubernetes API
(e.g. the CockroachDB certificate self-signer job) must therefore also be
allowed egress to the apiserver.

**This is not optional and cannot be done with an `ipBlock` rule.** On this
cluster the kube-apiserver is **self-hosted** (a static pod on the node), so
the `kubernetes` Service backend is the **node IP**, not a pod IP. Cilium
CIDR selectors ignore node addressing by default
(`--policy-cidr-match-mode` excludes `nodes`), so an egress `ipBlock:
0.0.0.0/0` rule never matches the apiserver. DNS happens to work because
CoreDNS is a normal pod whose return path stays in-cluster.

The correct mechanism is Cilium's `kube-apiserver` **entity**, applied
cluster-wide once in the platform (see
`infra/kubernetes/platform/networkpolicies/00-allow-kube-apiserver.yaml`):

```yaml
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-to-kube-apiserver
spec:
  endpointSelector:
    matchExpressions:
      - key: k8s:io.cilium.k8s.namespace.labels.kubernetes.io/metadata.name
        operator: In
        values:
          - prd-42wasd-admin
          - prd-games-42wasd-admin
          - prd-jya0
          - dev-42wasd-admin
          - dev-games-42wasd-admin
          - dev-jya0
          - mlops
  egress:
    - toEntities:
      - kube-apiserver
```

The `kube-apiserver` entity covers both in-cluster and out-of-cluster
deployments.

> **CRITICAL — do not use `endpointSelector: {}` here.** In Cilium, *any*
> endpoint selected by a policy becomes default-deny for traffic the policy
> does not explicitly allow. A blanket `endpointSelector: {}` therefore makes
> **every** pod in the cluster (including `kube-system` and `ingress`) egress
> default-deny, silently cutting world/internet egress for system namespaces
> that were never meant to be default-deny. This exact mistake took down the
> Cloudflare tunnel, CoreDNS upstream resolution, and app jar downloads
> (2026-08-24 incident, commit `c9795ad`).
>
> Scope the selector to **only** the tenant namespaces that already carry a
> `default-deny` NetworkPolicy and genuinely need the apiserver (the list
> above). Keep this list in sync with the platform per-namespace default-deny
> NetworkPolicies in `platform-networkpolicies`.

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

Cilium-specific egress controls can later enforce home-LAN exclusions more
precisely.

---