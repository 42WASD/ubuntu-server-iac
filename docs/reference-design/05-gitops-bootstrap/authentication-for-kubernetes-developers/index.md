# authentication for Kubernetes developers

Do not distribute the admin kubeconfig.

Short-term, for a small team, you can issue individual Kubernetes client credentials.

Long-term, use OIDC.

Target model:

```text
identity provider
    -> group tenant-jya0
    -> group tenant-42wasd-admin
    -> group gpu-approved
```

RKE2 API is reachable only through private management networking.

OIDC handles identity.

Kubernetes RBAC handles authorization.

This step may be postponed until the first external developer exists, but **do not solve it by copying `/etc/rancher/rke2/rke2.yaml`**.

## 27.1 Chosen approach (pending implementation)

| Decision | Choice | Rationale |
|---|---|---|
| Identity provider | **Dex (in-cluster, via Argo CD)** | Cloudflare Access is an access proxy, not a standard OIDC IdP; it cannot serve the Kubernetes `--oidc-*` token endpoints or a device-authorization grant for `kubelogin`. Dex is the standard in-cluster OIDC provider. |
| User backend | **GitHub OAuth connector** | Login with existing GitHub identity. GitHub org/team membership maps to Kubernetes groups. |
| Headless login on alpha | **kubelogin device-code flow (RFC 8628)** | Headless-friendly: the CLI prints a URL + code, the developer approves on any device's browser, and the token returns to alpha. No browser required on the headless server. |
| Kubernetes API reachability | **Tailscale only (for now)** | Keep `kube-apiserver` on the private management network. Cloudflare Tunnel is deferred to Phase 46; may expose the API later for alternative access. |

### 27.1.1 Component wiring

```text
GitHub account (developer)
    |  OAuth
    v
Dex (in-cluster, Argo CD)
    |  OIDC issuer (HTTPS on the node's own tailnet FQDN:
    |  https://alpha.taild82ced.ts.net — Tailscale certs cover ONLY the
    |  node FQDN, no subdomains; Traefik serves the issuer on 443)
    |  device-code flow via kubelogin
    v
kube-apiserver --oidc-issuer-url / --oidc-client-id
    |  username-claim=email, groups-claim=groups
    v
Kubernetes RBAC (Phase 26 RoleBindings by group)
    tenant-jya0 / tenant-42wasd-admin
```

### 27.1.2 Implementation steps (deferred)

1. **RKE2 OIDC flags** — add to `rke2_server` role config: `--oidc-issuer-url`, `--oidc-client-id`, `--oidc-username-claim=email`, `--oidc-groups-claim=groups`; restart `rke2-server`.
2. **Dex issuer TLS** — serve the issuer over HTTPS on the tailnet using the Tailscale cert for the **node's own FQDN** (`alpha.taild82ced.ts.net`; subdomains like `dex.alpha.…` are rejected by Tailscale cert issuance), routed via Traefik 443, so the device-code verification page loads in the browser.
3. **Deploy Dex via Argo CD** — new child app; GitHub connector; GitHub OAuth `client_id`/`client_secret` stored as a Kubernetes Secret, **never in Git**.
4. **Map GitHub identity → groups** — Dex `groups` claim must produce `tenant-jya0` / `tenant-42wasd-admin` so the Phase 26 RoleBindings apply.
5. **Install kubelogin + kubeconfig** — `kubectl oidc-login` (device flow) as an exec credential plugin in each developer kubeconfig.

### 27.1.3 Not doing

- Do **not** expose `kube-apiserver` publicly yet.
- Do **not** store the GitHub OAuth secret or Dex signing key in Git.
- Do **not** use Cloudflare Access as the Kubernetes OIDC IdP (it is not a standard OIDC provider for `kubelogin`).

### 27.1.4 Context model (every tenant namespace pre-configured)

Each developer kubeconfig ships with **one context per tenant namespace** in
addition to the default dev context. This is the ergonomic core of the OIDC
setup: developers switch between namespaces with a single
`kubectl config use-context <name>` instead of typing `-n` or hand-editing
contexts.

Design rules (research-backed):

- **Always set `user:` on every context.** The exec credential (kubelogin
  device-code) is what authenticates. A context created with
  `kubectl config set-context <n> --cluster=alpha --namespace=<ns>` leaves
  `user:` empty and kubectl falls back to a **basic-auth prompt**
  (`Please enter Username`). Every pre-rendered context reuses the SAME exec
  `user:` — only the `namespace:` differs.
- **Encode environment into the context name** so switching is unambiguous
  and deployment-safe. Generic names (`dev`, `test`) are ambiguous; descriptive
  `CLUSTER-LANE` names make the target clear at a glance.
- **Keep a safe default.** `current-context` points at the dev namespace so a
  new shell always lands somewhere least-privileged by default; the developer
  opts into other namespaces with `use-context`.

The tenant group `42WASD:tenant-42wasd-admin` can reach exactly these
namespaces, so exactly these contexts are pre-configured (all on cluster
`alpha`, all under the same exec user):

| Context name | Namespace | Access |
|---|---|---|
| `alpha-dev` | `dev-42wasd-admin` | developer (write) |
| `alpha-prd` | `prd-42wasd-admin` | reader |
| `alpha-games-dev` | `dev-games-42wasd-admin` | developer (write) |
| `alpha-games-prd` | `prd-games-42wasd-admin` | reader |
| `alpha-mlops` | `mlops` | reader |

The list is data-driven in the `developer_kubeconfig` role
(`developer_kubeconfig_contexts` in `defaults/main.yml`) and rendered by
`templates/kubeconfig.j2`, so adding a namespace is a one-line change. When a
new tenant is onboarded, the same pattern applies: enumerate its namespaces and
render one context per namespace.

```bash
kubectl config get-contexts                  # alpha, alpha-prd, alpha-games-dev, ...
kubectl config use-context alpha-games-prd
kubectl get pods                             # -> prd-games-42wasd-admin (reader)
```

---
