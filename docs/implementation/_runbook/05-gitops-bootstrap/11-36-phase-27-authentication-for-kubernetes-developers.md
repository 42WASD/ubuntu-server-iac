---
phase: 05-gitops-bootstrap/authentication-for-kubernetes-developers
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
# from infra/ (run as root to avoid become password prompt)
cd /home/jyao/ubuntu-server-iac/infra
sudo ansible-playbook -i inventory/production.yml ansible/site.yml \
  --limit alpha --connection local --tags kubeconfig
```

Deployed on alpha as root (become is then a root→root no-op; `--connection
local` since alpha has no passwordless self-SSH; `--limit alpha` skips the
unreachable `build01`). Result: `PLAY RECAP alpha ok=7 changed=2 failed=0`.

Verified the rendered kubeconfig is functionally identical to the hand-made
`config-oidc-jyao-42admin` (same `client` exec block, server, and CA; only the
context/user name differs). Each developer then runs
`kubectl oidc-login get-token --grant-type=device-code` (auto-invoked by the
exec credential) once, and `kubectl` works.

Deployment notes / bugs hit on first run:

- The role must create `/home/<user>/.kube` (mode `0700`) first — only
  `ehammoud` had it. Added an explicit `ansible.builtin.file` task.
- All tasks must carry the `kubeconfig` tag, otherwise `--tags kubeconfig`
  skips the `slurp`/`set_fact` that populates `developer_kubeconfig_ca_data`
  ("undefined" error).
- The template loop `{%- for %}` trimming collapsed `--oidc-extra-scope` and
  `command: kubectl` onto one line. Fixed by using `{% for %}` with
  `trim_blocks`/`lstrip_blocks` (content on the loop line).

Each developer now has `/home/<user>/.kube/config` (owner/user, mode `0600`)
with a valid OIDC exec credential.

### First-time login must use `exec:` + device-code (critical fix)

Two bugs surfaced only when an actual developer ran `kubectl` (the earlier
"final verification" had injected a raw `token:` directly, so the credential
plugin path was never exercised):

1. **`user.client:` is not a kubectl credential key.** The template rendered
   the kubelogin plugin under `user.client:`, which kubectl does not recognize.
   kubectl then got a 401 and fell back to a **basic-auth username/password
   prompt** (`Please enter Username/Password`). Fix: use `user.exec:` (the
   schema `kubectl config set-credentials --exec-*` produces), with
   `interactiveMode: IfAvailable` and `provideClusterInfo: true` at the `exec:`
   level.

2. **Authorization-code flow vs device-code.** Without `--grant-type`, kubelogin
   used the authcode-browser flow and failed headless (`could not open the
   browser`). Fix: add `--grant-type=device-code` so it prints a device URL/code:

   ```text
   Please visit the following URL in your browser manually:
   https://alpha.taild82ced.ts.net/device?user_code=DFSH-RHHS
   ```

Verified: after the fix, `sudo -u jyao-42admin kubectl get pods` invokes
kubelogin's device flow and prints the device URL (no more basic-auth prompt).

### Missing `email` scope → `Unauthorized` after a successful device login

Symptom: the Dex pod log showed `login successful ... groups=[42WASD:tenant-42wasd-admin]`, the kubelogin cache held a valid 24h ID token with the right `groups` claim, yet `kubectl auth whoami` returned `You must be logged in to the server (Unauthorized)`.

Root cause: the deployed kubeconfig only requested the `groups` extra scope,
so the issued ID token had **no `email` claim**. But kube-apiserver was
configured with `--oidc-username-claim=email`, so the OIDC authenticator could
not extract a username and rejected the token (401). The token was valid and
signed; the *claim set* was simply incomplete for the apiserver's username
claim.

```bash
# Decode the cached ID token (kubelogin cache) to confirm missing email claim:
sudo -n cat /home/<dev>/.kube/cache/oidc-login/<hash> \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id_token'])" \
  | cut -d. -f2 | base64 -d 2>/dev/null   # shows keys iss,sub,aud,exp,groups — NO email
```

Fix: add `email` to the requested extra scopes so the ID token carries the
claim the apiserver's `--oidc-username-claim=email` expects.

```bash
# infra/ansible/roles/developer_kubeconfig/defaults/main.yml
developer_kubeconfig_extra_scopes: "{{ rke2_oidc_extra_scopes | default(['groups', 'email']) }}"
```

Redeploy the role (creates the config with the extra `--oidc-extra-scope=email`
arg), then each developer re-runs the device-code flow. After re-login the
decoded token includes `email` and `kubectl auth whoami` succeeds. Also
back-ported the fix to the reference template
`infra/kubernetes/platform/dex/developer-kubeconfig.template.yaml` (which still
had the older `client:` block + `groups`-only scope).

### `stdout_callback = yaml` removed plugin → playbook failed to start

Redeploying the role with the system-wide `ansible-core 2.20.1` failed before
any task ran:

```
[ERROR]: The 'community.general.yaml' callback plugin has been removed.
  The plugin has been superseded by the option `result_format=yaml` in
  callback plugin ansible.builtin.default from ansible-core 2.13 onwards.
```

`infra/ansible/ansible.cfg` still referenced the old
`stdout_callback = yaml`, which pointed at a plugin removed from
`community.general` v12. Fix:

```ini
stdout_callback = default
result_format = yaml
```

### Final end-to-end verification

With the ID token written directly into a kubeconfig (`token:`), `kubectl`
resolves the real user and group and RBAC is enforced:

```bash
kubectl auth whoami
# Username: jinxiuyao@gmail.com
# Groups:   [42WASD:tenant-42wasd-admin system:authenticated]

kubectl get pods -n dev-42wasd-admin   # allowed  -> sees meme-site
kubectl get cm -n prd-42wasd-admin     # allowed  (reader)
kubectl get ns                          # names visible (see namespace-viewer below)
```

This confirms least-privilege: the developer can operate only their
tenant namespaces, not cluster-scoped resources.

### Namespace discoverability (tenant-namespace-viewer)

A developer with only namespace-scoped RoleBindings **cannot** `kubectl get
namespaces` — the Namespace object is cluster-scoped (see
kubernetes/kubernetes#112686). So developers had no way to see which
namespaces to switch to. Added a `ClusterRole` + `ClusterRoleBinding` bound to
the OIDC group `42WASD:tenant-42wasd-admin` in
`infra/kubernetes/platform/rbac/namespace-viewers.yaml`.

**Kubernetes RBAC limitation (honest scope):** `resourceNames` is not
compatible with the `list` verb (a list request has an empty resource name), so
no RBAC construct can make `kubectl get namespaces` return *only* the tenant's
namespaces. The ClusterRole therefore:

- grants `list` on `namespaces` broadly (reveals namespace NAMES only — grants
  NO access inside any namespace; in-namespace access stays enforced by the
  per-namespace `tenant-developer` / `tenant-reader` RoleBindings), and
- grants `get`/`watch` on `namespaces` scoped to the tenant's own namespaces via
  `resourceNames` (`dev-42wasd-admin`, `prd-42wasd-admin`,
  `dev-games-42wasd-admin`, `prd-games-42wasd-admin`, `mlops`).

```bash
# As the developer:
kubectl get namespaces                  # -> all names, for context switching
kubectl get ns dev-42wasd-admin          # -> ok (tenant ns, resourceNames)
kubectl get ns kube-system               # -> FORBIDDEN (get scoped to tenant ns)
kubectl get pods -n kube-system          # -> FORBIDDEN (list ns grants no in-ns access)
kubectl get secrets -n dev-42wasd-admin  # -> FORBIDDEN (dev role has no secrets)
```

Apply/sync: Argo CD `platform-rbac` app picks it up from the `rbac/` path
(manual for the first apply).

### Default namespace in the developer kubeconfig

By default, `kubectl` operates in the `default` namespace, which the tenant
group has no access to. Set the context's `namespace:` so every `kubectl`
command targets the tenant's dev namespace by default:

```yaml
# infra/ansible/roles/developer_kubeconfig/defaults/main.yml
developer_kubeconfig_namespace: "dev-42wasd-admin"

# templates/kubeconfig.j2
contexts:
- name: {{ developer_kubeconfig_cluster_name }}
  context:
    cluster: {{ developer_kubeconfig_cluster_name }}
    user: {{ developer_kubeconfig_user }}
    namespace: {{ developer_kubeconfig_namespace }}
```

Redeploy with `--tags kubeconfig`, then verify (no `-n` needed):

```bash
$ kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}'
# dev-42wasd-admin
kubectl get pods          # -> meme-site (defaults to dev-42wasd-admin)
```

Also back-ported to `infra/kubernetes/platform/dex/developer-kubeconfig.template.yaml`.

### Pre-configured contexts for every tenant namespace

A developer who wants to operate a namespace other than the default had to
create a context by hand — and the naive command drops `user:`, leaving an
empty user that makes kubectl fall back to a basic-auth prompt:

```text
# WRONG: no --user -> context has user:"" -> "Please enter Username:" prompt
kubectl config set-context 42wasd-prd --cluster=alpha --namespace=prd-42wasd-admin
```

The role now pre-renders a context for **every** namespace the
`42WASD:tenant-42wasd-admin` group can reach, each reusing the SAME exec user
(the device-code credential), so switching is just `kubectl config use-context`.

`defaults/main.yml` drives the list:

```yaml
# infra/ansible/roles/developer_kubeconfig/defaults/main.yml
developer_kubeconfig_contexts:
  - name: dev            # -> alpha-dev            -> dev-42wasd-admin
  - name: prd            # -> alpha-prd            -> prd-42wasd-admin
  - name: games-dev      # -> alpha-games-dev      -> dev-games-42wasd-admin
  - name: games-prd      # -> alpha-games-prd      -> prd-games-42wasd-admin
  - name: mlops          # -> alpha-mlops          -> mlops
```

Each rendered context is `cluster: alpha`, `user: <dev>` (the exec credential),
`namespace: <ns>`; names follow the `CLUSTER-LANE` convention so they are
descriptive and unambiguous. `templates/kubeconfig.j2` loops over the list and
emits a block per entry, always setting `user: {{ developer_kubeconfig_user }}`
— never leaving it empty.

Redeploy (`--tags kubeconfig`), then as a developer:

```bash
kubectl config get-contexts                  # -> jyao-42admin, alpha-dev,
                                             #    alpha-prd, alpha-games-dev,
                                             #    alpha-games-prd, alpha-mlops
kubectl config use-context alpha-prd
kubectl get pods                             # -> prd-42wasd-admin (reader)
kubectl config use-context alpha-dev
kubectl get pods                             # -> dev-42wasd-admin (meme-site)
```

The `current-context` stays `jyao-42admin` (the default dev namespace) so new
shells land somewhere safe; developers opt into another namespace with
`use-context`. Back-ported to
`infra/kubernetes/platform/dex/developer-kubeconfig.template.yaml`.

Verified locally by rendering the template with jinja2 and parsing the result
as YAML — every one of the 6 contexts (the default + `alpha-dev`, `alpha-prd`,
`alpha-games-dev`, `alpha-games-prd`, `alpha-mlops`) carries a non-empty
`user:` and the correct `namespace:`:

```bash
source projects/.venv/bin/activate
python - <<'EOF'   # render kubeconfig.j2 -> yaml.safe_load -> assert each context.user
...
EOF
# jyao-42admin    -> dev-42wasd-admin       user=OK
# alpha-dev       -> dev-42wasd-admin       user=OK
# alpha-prd       -> prd-42wasd-admin       user=OK
# alpha-games-dev -> dev-games-42wasd-admin user=OK
# alpha-games-prd -> prd-games-42wasd-admin user=OK
# alpha-mlops     -> mlops                  user=OK
# VALID YAML: OK
```

Deployed live to all 4 developers:

```bash
cd /home/jyao/ubuntu-server-iac/infra
sudo ansible-playbook -i inventory/production.yml ansible/site.yml \
  --limit alpha --connection local --tags kubeconfig
# PLAY RECAP alpha: ok=7 changed=1 failed=0  (4 kubeconfigs re-rendered)
```

Verified on alpha as a developer (all 6 contexts present, default marked `*`):

```text
CURRENT   NAME              CLUSTER   AUTHINFO       NAMESPACE
          alpha-dev         alpha     jyao-42admin   dev-42wasd-admin
          alpha-games-dev   alpha     jyao-42admin   dev-games-42wasd-admin
          alpha-games-prd   alpha     jyao-42admin   prd-games-42wasd-admin
          alpha-mlops       alpha     jyao-42admin   mlops
          alpha-prd         alpha     jyao-42admin   prd-42wasd-admin
*         jyao-42admin      alpha     jyao-42admin   dev-42wasd-admin
```

And a non-default context authenticates end-to-end (reader, empty ns):

```bash
kubectl config use-context alpha-prd
kubectl get pods -n prd-42wasd-admin   # -> No resources found in prd-42wasd-admin namespace
```

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
