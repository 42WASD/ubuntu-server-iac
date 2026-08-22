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

## 27.5 Developer login (per developer)

1. Install the kubelogin plugin (separate binary exposing `kubectl oidc-login`).
   For Linux amd64 on the host, kubelogin `v1.36.3`:

   ```bash
   cd /tmp
   curl -sL -o kubelogin.zip \
     https://github.com/int128/kubelogin/releases/download/v1.36.3/kubelogin_linux_amd64.zip
   unzip -o -q kubelogin.zip
   sudo cp kubelogin /usr/local/bin/kubectl-oidc_login && sudo chmod +x /usr/local/bin/kubectl-oidc_login
   kubectl oidc-login version
   ```

2. Create a kubeconfig for the developer with the OIDC exec credential. Reuse
   the cluster CA from the admin config (`sudo cat /etc/rancher/rke2/rke2.yaml`,
   `certificate-authority-data`), point the server at
   `https://alpha.taild82ced.ts.net:6443`, and use the device-code grant:

   ```bash
   CA=$(sudo cat /etc/rancher/rke2/rke2.yaml | grep 'certificate-authority-data:' | awk '{print $2}')
   cat > ~/.kube/config-oidc-jyao-42admin <<EOF
   apiVersion: v1
   kind: Config
   clusters:
   - cluster:
       certificate-authority-data: $CA
       server: https://alpha.taild82ced.ts.net:6443
     name: alpha
   contexts:
   - context: { cluster: alpha, user: jyao-42admin }
     name: jyao-42admin
   current-context: jyao-42admin
   users:
   - name: jyao-42admin
     user:
       exec:
         apiVersion: client.authentication.k8s.io/v1
         args:
         - oidc-login
         - get-token
         - --oidc-issuer-url=https://alpha.taild82ced.ts.net
         - --oidc-client-id=kubernetes
         command: kubectl
         interactiveMode: IfAvailable
         provideClusterInfo: true
   EOF
   ```

   > Do **not** embed a `client-secret` — the `kubernetes` Dex client uses the
   > public device-code grant (RFC 8628), so there is none to leak.

3. Log in with the device-code grant (headless-friendly; prints a URL + code
   because no browser is available on the host):

   ```bash
   KUBECONFIG=~/.kube/config-oidc-jyao-42admin \
     kubectl oidc-login get-token --grant-type=device-code \
     --oidc-issuer-url=https://alpha.taild82ced.ts.net --oidc-client-id=kubernetes
   ```

   Open `https://alpha.taild82ced.ts.net/device?user_code=<CODE>` in any
   browser, approve on GitHub as a member of `tenant-jya0` /
   `tenant-42wasd-admin`, and the token is written back to the kubeconfig.

4. Verify identity + groups reach the API server:

   ```bash
   KUBECONFIG=~/.kube/config-oidc-jyao-42admin kubectl auth whoami
   KUBECONFIG=~/.kube/config-oidc-jyao-42admin kubectl get pods
   ```

### Device-code flow requires `/device/callback`

Dex's device authorization flow (RFC 8628) redirects the browser to
`/device/callback` while a GitHub connector auth is in flight. That path must
be listed in the static client's `redirectURIs` — otherwise Dex returns
**`Unregistered redirect_uri`** and the code never exchanges. Added
`"/device/callback"` to the `kubernetes` client. Verified end-to-end: the Dex
pod log showed the connector rejecting only on team membership, i.e. the whole
chain (device code → GitHub OAuth → Dex → groups claim) works.

### Device client must be `public: true` (invalid_client fix)

When the browser callback `/device/callback` returned
`{"error":"invalid_client","error_description":"Invalid client credentials."}`
the Dex pod log still showed `login successful` with the right groups — so
GitHub auth worked but the **client binding** failed. Root cause (from Dex
source `server/device/device.go`, `completeDeviceAuthorization`):

```go
// Constant-time comparison of the client secret.
if subtle.ConstantTimeCompare([]byte(client.Secret), []byte(deviceReq.ClientSecret)) != 1 {
    return invalid_client
}
```

The device-code flow never sends a `client_secret`, but the `kubernetes`
client was configured with `secretEnv: DEX_CLIENT_SECRET`, so
`client.Secret != deviceReq.ClientSecret` (empty) → `invalid_client`.

**Fix** (matches Dex's own `examples/config-dev.yaml`, which marks its
device-flow client `public: true`): drop the secret and mark the client
`public: true` so `client.Secret` is empty and the comparison passes.

```yaml
- id: kubernetes
  name: Kubernetes
  public: true          # device-code flow sends no secret; must be a public client
  redirectURIs: [ ..., "/device/callback" ]
  publicGrantTypes: ["urn:ietf:params:oauth:grant-type:device_code"]
```

Also removed the now-unused `DEX_CLIENT_SECRET` env + `dex-client` Secret ref
from the Deployment. Committed as `b27fceb`. After this, the browser flow
returned **"Login Successful for Kubernetes"**.

### Client-side token verification (manual device exchange)

`kubectl oidc-login` hangs in a headless terminal (no `xdg-open`), so verify
the flow manually with curl. Request a device code, approve it in a browser,
then poll the token endpoint:

```bash
# 1. Request a device code (scope must include what the apiserver needs:
#    email for --oidc-username-claim=email, groups for --oidc-groups-claim=groups)
curl -sk -X POST https://alpha.taild82ced.ts.net/device/code \
  -d "client_id=kubernetes&scope=openid email groups"
# => user_code=XXXX-XXXX, device_code=...

# 2. Authorize in a browser: https://alpha.taild82ced.ts.net/device?user_code=<USER_CODE>

# 3. Exchange device_code for tokens
curl -sk -X POST https://alpha.taild82ced.ts.net/token \
  -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
  -d "device_code=<DEVICE_CODE>" -d "client_id=kubernetes"
# => id_token with iss, aud=kubernetes, email, groups

# 4. Decode the ID token (JWT payload) to confirm claims:
#    iss=https://alpha.taild82ced.ts.net, aud=kubernetes,
#    email=<user email>, groups=["42WASD:tenant-42wasd-admin"]
```

A token requested with only `scope=openid` omits `email` and `groups`; request
`openid email groups` (which is what kubelogin's default `--oidc-extra-scope`
sends).

### `oidc: authenticator not initialized` — restart kube-apiserver

A `TokenReview` against a valid Dex ID token returned:

```json
{ "error": "[invalid bearer token, oidc: authenticator not initialized]" }
```

The kube-apiserver's OIDC authenticator failed to **initialize at startup**
(because the issuer `https://alpha.taild82ced.ts.net` via Dex/Traefik was not
yet reachable when the apiserver booted). When that happens the apiserver
silently disables OIDC and rejects every ID token, even ones with valid
signature/issuer/aud (verified via `/keys` `kid` match). Fix: restart the
control plane once the issuer is healthy:

```bash
kubectl -n security get deploy dex          # 1/1 Running
curl -s https://alpha.taild82ced.ts.net/.well-known/openid-configuration  # 200
sudo systemctl restart rke2-server
```

After restart, re-test with the manual token exchange from above then
`kubectl auth whoami`.

**Real root cause (beyond the restart): apiserver cannot resolve the Tailscale
issuer hostname.** Even after `systemctl restart rke2-server`, the TokenReview
still failed. The apiserver container logs showed:

```
oidc authenticator: initializing plugin: Get "https://alpha.taild82ced.ts.net/...
 dial tcp: lookup alpha.taild82ced.ts.net on 8.8.8.8:53: no such host
```

The kube-apiserver **static-pod container** gets a generated `resolv.conf`
pointing at `8.8.8.8`, which cannot resolve the Tailscale **MagicDNS** name.
The host resolves it fine (systemd-resolved `127.0.0.53` → MagicDNS →
`100.112.202.47`), but the container does not. Fix: mount the host
`resolv.conf` into the apiserver via RKE2's `kube-apiserver-extra-mount`:

```bash
# /etc/rancher/rke2/config.yaml  (mirrored in the rke2_server role template)
kube-apiserver-extra-mount:
  - "/etc/resolv.conf:/etc/resolv.conf:ro"
sudo systemctl restart rke2-server
```

Optional belt-and-braces: pin the hostname in `/etc/hosts`
(`100.112.202.47 alpha.taild82ced.ts.net`). After the resolv mount, the OIDC
authenticator initializes and a `TokenReview` succeeds:

```json
{"authenticated":true,"user":{"groups":["42WASD:tenant-42wasd-admin","system:authenticated"],"username":"jinxiuyao@gmail.com"}}
```

### Automated distribution via the `developer_kubeconfig` role

To onboard all tenant developers in one GitOps-reproducible step, a new
Ansible role `infra/ansible/roles/developer_kubeconfig/` renders and deploys a
kubeconfig to each developer's `~/.kube/config`:

- `defaults/main.yml` — `developer_kubeconfig_users` lists the Linux usernames
  (jyao-42admin, ehammoud, mayan, mtangalv). It derives the OIDC issuer, client
  id, extra scopes, and API server address from the RKE2 role vars
  (`rke2_oidc_*`, `rke2_admin_kubeconfig_server`) so there is a single source
  of truth, with explicit fallbacks so the role is runnable standalone.
- `tasks/main.yml` — slurps the root-only RKE2 admin kubeconfig
  (`/etc/rancher/rke2/rke2.yaml`) and extracts `certificate-authority-data`
  **live**, so the CA is never committed to Git. Then renders the kubeconfig
  template per user and writes it to `/home/<user>/.kube/config` mode `0600`.
- `templates/kubeconfig.j2` — embeds the OIDC `kubectl oidc-login` exec
  credential. Content is identical for every developer except the cosmetic
  context/user NAME; the real identity is resolved by kubelogin under each OS
  user's home (device-code flow, so no per-user secret).
- `site.yml` — a dedicated play runs `developer_kubeconfig` on `rke2_servers`
  after `rke2_server`.

```bash
# from infra/
cd /home/jyao/ubuntu-server-iac/infra
ansible-playbook -i inventory/production.yml ansible/site.yml --limit alpha \
  --tags kubeconfig
```

Verified: the rendered kubeconfig is functionally identical to the hand-made
`config-oidc-jyao-42admin` (same `client` exec block, server, and CA; only the
context/user name differs). Each developer then runs
`kubectl oidc-login get-token --grant-type=device-code` (auto-invoked by the
exec credential) once, and `kubectl` works.

### Final end-to-end verification

With the ID token written directly into a kubeconfig (`token:`), `kubectl`
resolves the real user and group and RBAC is enforced:

```bash
kubectl auth whoami
# Username: jinxiuyao@gmail.com
# Groups:   [42WASD:tenant-42wasd-admin system:authenticated]

kubectl get pods -n dev-42wasd-admin   # allowed  -> sees meme-site
kubectl get cm -n prd-42wasd-admin     # allowed  (reader)
kubectl get ns                          # FORBIDDEN (cluster scope)
```

This confirms least-privilege: the developer can operate only their
tenant namespaces, not cluster-scoped resources.

## 27.6 Verification

```bash
kubectl -n security get pods -l app=dex            # 1/1 Running
kubectl -n argocd get app platform-dex             # Synced  Healthy
curl -sk https://alpha.taild82ced.ts.net/.well-known/openid-configuration
```
### Git credential helper cleanup (local gh → system-wide gh)

The `gh` CLI was moved from `/home/jyao/.local/bin/gh` to `/usr/local/bin/gh`
so all users can access it. This left stale URL-scoped credential helpers in
`~/.gitconfig` pointing at the deleted path:

```bash
# showed: helper = !/home/jyao/.local/bin/gh auth git-credential
git config --global --unset-all credential.https://github.com.helper
git config --global --unset-all credential.https://gist.github.com.helper
git config --global credential.https://github.com.helper '/usr/local/bin/gh auth git-credential'
git config --global credential.https://gist.github.com.helper '/usr/local/bin/gh auth git-credential'
```

Verified all three helpers now point to `/usr/local/bin/gh`, and `git fetch`
authenticates successfully.
