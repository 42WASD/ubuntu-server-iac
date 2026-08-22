---
phase: 05-gitops-bootstrap/11-36-phase-27-authentication-for-kubernetes-developers
---
# Phase 27 — authentication for Kubernetes developers (Dex + GitHub OIDC)

Implemented Dex as the in-cluster OIDC identity provider, wired to GitHub
OAuth, and configured `kube-apiserver` to authenticate via OIDC. Developers
use `kubectl oidc-login` (device-code flow, RFC 8628) for headless login on
the host.

## 27.1 Decisions

| Decision | Choice | Why |
|---|---|---|
| Issuer hostname | `https://alpha.taild82ced.ts.net` (port 443) | Tailscale issues certs **only for the node's own FQDN** — no subdomains (`tailscale cert dex.alpha…` → "invalid domain"). Traefik (default ingress, `websecure`/443) routes the issuer; kube-apiserver stays on 6443 → no port conflict. |
| Group mapping | Bind RBAC to `42WASD:<team>` | Dex GitHub groups are always `<org>:<team>` and cannot drop the org prefix. Updated Phase 26 RoleBindings to bind `42WASD:tenant-jya0` / `42WASD:tenant-42wasd-admin`. |
| Secrets | Manual `kubectl` provision | GitHub OAuth `client_id`/`secret` and the Dex client secret are never committed (no secrets tooling in repo yet). |
| TLS | Tailscale cert via Traefik | `sudo tailscale cert alpha.taild82ced.ts.net` works; store as a `tls` Secret `tailscale-cert`. |

## 27.2 Manifests

`infra/kubernetes/platform/dex/`:

- `deployment.yaml` — Dex `v2.45.1` Deployment (1 replica, SQLite on a
  `nvme-fast` PVC), `dex` Service (5556), ServiceAccount.
- `configmap.yaml` — Dex config: issuer, GitHub connector (org `42WASD`,
  teams `tenant-jya0` / `tenant-42wasd-admin`, `teamNameField: slug`),
  `staticClients` `kubernetes` with `publicGrantTypes` device-code.
- `ingress.yaml` — `IngressRoute` (Traefik) terminating TLS with the
  `tailscale-cert` Secret.

`infra/kubernetes/bootstrap/argocd/apps/platform-dex.yaml` — new Argo child
app (project `platform`, sync-wave `-3`, auto-discovered by `platform-root`).

`infra/kubernetes/platform/rbac/` — updated all RoleBinding subjects to
`42WASD:tenant-jya0` / `42WASD:tenant-42wasd-admin`.

`infra/ansible/roles/rke2_server/` — added `rke2_oidc_*` vars and
`kube-apiserver-arg` OIDC block (enabled via `rke2_oidc_enabled` in
`alpha.yml`).

## 27.3 Commands run

Validate the manifests server-side (dry-run):

```bash
cd infra/kubernetes/platform/dex
kubectl apply --dry-run=server -f deployment.yaml   # dex, service, pvc, sa
kubectl apply --dry-run=server -f configmap.yaml     # dex-config
kubectl apply --dry-run=server -f ingress.yaml        # ingressroute.traefik.io/dex
```

Provision the TLS Secret from the Tailscale cert (root-owned temp files):

```bash
sudo tailscale cert alpha.taild82ced.ts.net
kubectl -n security create secret tls tailscale-cert \
  --cert=alpha.taild82ced.ts.net.crt --key=alpha.taild82ced.ts.net.key \
  --dry-run=client -o yaml | kubectl apply -f -
rm -f alpha.taild82ced.ts.net.crt alpha.taild82ced.ts.net.key
```

Provision the GitHub OAuth + Dex client Secrets (values supplied interactively
by the developer, never committed):

```bash
kubectl -n security create secret generic dex-github-oauth \
  --from-literal=client-id='<GH_APP_CLIENT_ID>' \
  --from-literal=client-secret='<GH_APP_CLIENT_SECRET>' \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n security create secret generic dex-client \
  --from-literal=client-secret='<RANDOM_LONG_SECRET>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

Sync via Argo CD (refresh root, then sync the child app):

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
kubectl -n argocd patch application platform-dex \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"apply":{"force":true}}}}}'
```

### Debug fixes

1. **Dex CrashLoopBackOff — SQLite write permission.** Fresh hostpath/LVM
   PVC is root-owned but the Dex image runs as UID 1000. Fixed with a pod
   `securityContext` on the Deployment (`runAsUser: 1000, runAsGroup: 1000,
   fsGroup: 1000`). Had to force-delete the old pod to release the RWO PVC
   before the fixed pod could mount.

2. **Issuer 404 with the default Traefik cert.** RKE2's bundled Traefik runs
   with `--providers.kubernetescrd.ingressClass=traefik`, so an IngressRoute
   without `spec.ingressClassName: traefik` is **ignored** (default cert +
   404). Added `ingressClassName: traefik`, dropped the redundant
   `traefik.ingress.kubernetes.io/router.entrypoints` annotation and the
   `PathPrefix('/')` from the Host rule. Verified issuer returns 200 with the
   Let's Encrypt cert for `CN=alpha.tail.iota.ts.net`.

### 27.3.1 Apply the RKE2 OIDC flags (control-plane change)

RKE2 renders its config from `/etc/rancher/rke2/config.yaml`. Add the
`kube-apiserver-arg` block, validate YAML, then restart `rke2-server` (brief
API downtime). A timestamped backup is written before editing.

```bash
sudo cp /etc/rancher/rke2/config.yaml /etc/rancher/rke2/config.yaml.bak-$(date +%Y%m%d-%H%M%S)
# insert the kube-apiserver-arg OIDC block (see 27.2 manifests / role template)
sudo python3 - <<'PY'
from pathlib import Path
p = Path('/etc/rancher/rke2/config.yaml')
txt = p.read_text()
block = '''
# OIDC (Dex + GitHub, Phase 27). Issuer must match the tailnet-visible Dex URL
# that kubelogin discovers. API stays on the tailnet only (port 6443); the
# issuer is served over HTTPS via Traefik.
kube-apiserver-arg:
  - "oidc-issuer-url=https://alpha.taild82ced.ts.net"
  - "oidc-client-id=kubernetes"
  - "oidc-username-claim=email"
  - "oidc-groups-claim=groups"
'''
marker = '# Admin kubeconfig remains root/platform-admin controlled.'
if 'oidc-issuer-url' not in txt:
    p.write_text(txt.replace(marker, block + marker))
PY

sudo python3 -c "import yaml; yaml.safe_load(open('/etc/rancher/rke2/config.yaml'))"  # validate
sudo systemctl restart rke2-server
```

Verify the flags landed on the running process and the cluster is healthy:

```bash
sudo ps aux | grep kube-apiserver | grep -o "oidc-[a-z-]*=[^ ]*" | sort -u
# oidc-client-id=kubernetes
# oidc-groups-claim=groups
# oidc-issuer-url=https://alpha.taild82ced.ts.net
# oidc-username-claim=email
kubectl cluster-info && kubectl get nodes    # api up, node Ready
```

## 27.5 Developer login (manual, per developer)

1. Install the kubelogin plugin (separate binary; `kubectl oidc-login`).
2. Create a kubeconfig for the developer with the OIDC exec credential:
   `idp-issuer-url=https://alpha.taild82ced.ts.net`, `client-id=kubernetes`,
   `exec: kubectl oidc-login get-token`.
3. On first use, `kubectl` opens the device-code flow: prints a URL + code;
   the developer approves on any device's browser; the token returns to
   alpha.

## 27.5 Verification

```bash
kubectl -n security get pods -l app=dex            # 1/1 Running
kubectl -n argocd get app platform-dex             # Synced  Healthy
curl -sk https://alpha.taild82ced.ts.net/.well-known/openid-configuration
```