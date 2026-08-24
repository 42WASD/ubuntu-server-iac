---
phase: 05-gitops-bootstrap/default-deny-networkpolicy
---

# Phase 25 — default-deny NetworkPolicy

Added a `default-deny` NetworkPolicy (Ingress + Egress) to every tenant
namespace, plus an `allow-cluster-dns` egress rule so workloads can still
resolve CoreDNS. Additional per-application flows are added later as needed.

## 25.1 Manifests

`infra/kubernetes/platform/networkpolicies/`:

- `jya0.yaml` — `dev-jya0`, `prd-jya0`
- `42wasd-admin.yaml` — `dev-42wasd-admin`, `prd-42wasd-admin`, `mlops`
- `games.yaml` — `prd-games-42wasd-admin` (canonical) and
  `dev-games-42wasd-admin` (ephemeral staging)

Each namespace gets:

```yaml
# default-deny
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]

# allow-cluster-dns
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports: [UDP 53, TCP 53]
```

Enforced by the bundled Cilium CNI (network policy mode on).

Managed by a new Argo child app `platform-networkpolicies` (sync-wave `-5`)
in `infra/kubernetes/bootstrap/argocd/apps/platform-networkpolicies.yaml`.
The `platform-root` app auto-discovered it after a hard refresh.

## 25.2 Applied via Argo CD

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
# -> platform-networkpolicies  Synced  Healthy
```

Verified `default-deny` + `allow-cluster-dns` in every tenant namespace:

```bash
for ns in dev-jya0 prd-jya0 dev-42wasd-admin prd-42wasd-admin mlops \
          dev-games-42wasd-admin prd-games-42wasd-admin; do
  kubectl -n $ns get networkpolicies
done
```

The existing `demo-meme` workload lives in a separate non-tenant namespace
and is unaffected (still Running).

## 25.3 Every tenant must also reach the kube-apiserver

Because the apiserver is **self-hosted** (static pod on the node), the
`kubernetes` Service backend is the **node IP**, not a pod IP. Cilium CIDR
selectors ignore node addressing by default, so an egress `default-deny`
policy **cannot** allow the apiserver with an `ipBlock: 0.0.0.0/0` rule. The
correct mechanism is Cilium's `kube-apiserver` **entity**, applied once
cluster-wide in
`infra/kubernetes/platform/networkpolicies/00-allow-kube-apiserver.yaml`,
managed by the `platform-networkpolicies` Argo app.

```bash
kubectl get ciliumclusterwidenetworkpolicies.cilium.io allow-to-kube-apiserver
```

## 25.4 INCIDENT (2026-08-24): blanket `endpointSelector: {}` broke cluster egress

The CCNP was first applied with `endpointSelector: {}` (commit `c9795ad`).
In Cilium, **any** endpoint selected by a policy becomes default-deny for
traffic the policy does not explicitly allow. A blank `{}` selector therefore
made **every** pod in the cluster egress default-deny — including `kube-system`
and `ingress` namespaces that were never meant to be default-deny.

**Impact:** Cloudflare tunnel `CrashLoopBackOff` (SRV lookup `argotunnel.com`
timeout), CoreDNS `SERVFAIL` (blocked upstream to `8.8.8.8`), and app jar
downloads blocked (velocity / paper `ImagePullBackOff`).

**Detection** (Cilium monitor drops):

```text
identity 27913->world: 10.42.0.130:42608 -> 8.8.8.8:53 udp   (CoreDNS)
identity 1948->world: 10.42.0.106:41262 -> 1.1.1.1:853 tcp    (cloudflared)
```

**Fix (applied live + repo):** scoped the selector to only the tenant
namespaces that carry `default-deny` and genuinely need the apiserver:

```yaml
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

**Verify (restored egress):**

```bash
kubectl run -it --rm egress-check --image=curlimages/curl -- \
  curl -s -o /dev/null -w '%{http_code}\n' https://1.1.1.1
# -> 301
```

cloudflared back to `2/2 Running` with HTTP/2 connections to the Cloudflare
edge; tunnel endpoint returned `200`; DNS resolvable. (Cloudflare QUIC fails
but HTTP/2 TCP fallback works — acceptable.)

**Lesson:** never use `endpointSelector: {}` for an egress-only CCNP. Scope
to the specific tenant namespaces and keep the list in sync with the
per-namespace default-deny NetworkPolicies.