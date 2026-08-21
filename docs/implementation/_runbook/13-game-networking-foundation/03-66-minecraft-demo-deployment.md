---
phase: 13-game-networking-foundation/minecraft-demo-deployment
---
# Minecraft demo — dev deployment record

**Intent:** deploy a vanilla, cracked-mode (offline/unauthorized clients)
Minecraft server into the `dev-games-42wasd-admin` ephemeral lane as the first
concrete game workload, fully GitOps/Argo-managed and governed.

Reference: Part XIII (game networking) + research note in the workspace session
(`/memories/session/minecraft-demo-research.md`).

## 1. Image & mode

- Image: `itzg/minecraft-server:latest` (most-used MC image, Apache-2.0).
- Vanilla latest is auto-downloaded on first start (`TYPE=VANILLA`,
  `VERSION=LATEST`).
- Cracked mode: `ONLINE_MODE=FALSE` → any offline/unauthorized client can join.
- Non-root image user UID/GID 1000 → compatible with the restricted Pod
  Security profile when the pod sets `runAsNonRoot`, `runAsUser/Group: 1000`,
  `fsGroup: 1000`, `capabilities.drop: [ALL]`, seccomp `RuntimeDefault`,
  `allowPrivilegeEscalation: false`.

## 2. Files (repo)

`infra/kubernetes/tenants/minecraft-demo/`:

| File | Purpose |
|---|---|
| `deployment.yaml` | single-replica Recreate Deployment, 2G heap |
| `service.yaml` | **NodePort** 30079 → :25565 (game edge = UAE relay -> WireGuard -> NodePort) |
| `networkpolicy.yaml` | allow ingress 25565 + outbound internet (jar download) |
| `pvc.yaml` | 5Gi world volume on `nvme-fast` (now binds — Part VII complete) |
| `README.md` | ops notes |

Argo Application: `infra/kubernetes/bootstrap/argocd/apps/tenant-minecraft-demo.yaml`
(project `tenant-42wasd-admin`, destination `dev-games-42wasd-admin`).

## 3. Design notes

- **One replica + Recreate**: vanilla is a single in-memory process owning the
  world files on the PVC. `Recreate` guarantees a new pod never starts before
  the old one (which owns the world) is gone, avoiding two writers corrupting
  the level.
- **NodePort + UAE relay (game edge)**: the service was converted to a
  **NodePort** on `30079`. The UAE WireGuard relay VPS (`89.36.162.171`)
  DNATs its public `:25565` → tunnel peer `10.200.0.2:30079`, so external
  players hit the game edge through the tunnel. The Kyverno
  `restrict-exposure-and-image-tags` policy flags NodePort in **Audit** mode
  (records the flag, does not block).
- **Egress**: the games namespace is default-deny. On first start the image
  downloads the vanilla jar from Mojang, so the NetworkPolicy allows outbound
  internet for this workload. (Cluster DNS already allowed by platform
  `allow-cluster-dns`.)
- **PVC** now binds to `nvme-fast` because Part VII installed OpenEBS + the
  StorageClasses. (The original research note assumed it would stay Pending —
  that is no longer the case.)

## 4. Deploy

```bash
git add infra/kubernetes/tenants/minecraft-demo infra/kubernetes/bootstrap/argocd/apps/tenant-minecraft-demo.yaml
git commit -m "feat(games): Minecraft dev tenant - cracked vanilla server in dev-games"
git push
# app-of-apps picks it up; refresh + sync
kubectl -n argocd patch application platform-root --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
kubectl -n argocd patch application platform-root --type merge -p '{"operation":{"sync":{"syncStrategy":{"hook":{}}}}}'
```

## 5. Verified (live)

```text
$ kubectl -n argocd get application minecraft-demo
NAME             SYNC   HEALTH
minecraft-demo   Synced  Healthy

$ kubectl -n dev-games-42wasd-admin get all,pvc
pod/minecraft-demo-...  1/1 Running
service/minecraft-demo  ClusterIP 10.43.76.169  25565/TCP
deployment/minecraft-demo  1/1  1  1
persistentvolumeclaim/minecraft-demo-data  Bound  nvme-fast  5Gi
```

Server started cleanly (jar download + world gen):

```text
[Server thread/INFO]: Done (12.984s)! For help, type "help"
```

Cracked mode confirmed:

```text
$ grep -E "online-mode|server-port" /data/server.properties
online-mode=false
server-port=25565
```

TCP reachable on the ClusterIP:

```bash
timeout 5 bash -c 'echo > /dev/tcp/10.43.76.169/25565 && echo "PORT 25565 OPEN"'
```

## 5a. Game edge — UAE WireGuard relay (persisted)

The UAE relay VPS (`89.36.162.171`) forwards public `:25565` to the alpha
NodePort over the existing WireGuard tunnel (`10.200.0.2`).

**Boot-persistent pieces on the VPS:**

1. `/usr/local/bin/mc-relay-nat.sh` — idempotent script that adds the DNAT and
   MASQUERADE rules only if absent (safe to re-run).
2. `/etc/systemd/system/mc-relay-nat.service` — `oneshot`, `WantedBy
   multi-user.target`, `After wg-quick@wg0.service`. `Enabled`.
3. `/etc/wireguard/wg0.conf` `[Interface]` `PostUp = /usr/local/bin/mc-relay-nat.sh`
   — re-applies the rules every time `wg-quick up wg0` runs.

### Range-based relay (Option A)

Instead of one DNAT per game server, the VPS forwards a **reserved game
NodePort range** (`30000-30199`) straight through the tunnel. So a new game
server needs **only** a Service manifest with a NodePort in that range — no
iptables edit on the VPS.

Rules the script programs (idempotent via `iptables-save | grep`):

```text
PREROUTING  -d 89.36.162.171 -p tcp --dport 30000:30199 -j DNAT --to-destination 10.200.0.2
PREROUTING  -d 89.36.162.171 -p tcp --dport 25565     -j DNAT --to-destination 10.200.0.2:30079  # alias (back-compat)
POSTROUTING -d 10.200.0.2/32                          -j MASQUERADE                                 # one rule for whole peer
```

The single `MASQUERADE` covers the whole tunnel peer — no per-port MASQ rule.
The `25565` alias keeps existing player addresses working (they connect to
`89.36.162.171:25565` → minecraft NodePort).

**Kyverno guard:** rule `constrain-game-nodeport-range` in
`restrict-exposure-and-image-tags` (Audit mode) flags any game-namespace
NodePort outside `30000-30199`, so a Service can't silently pick a port the
relay doesn't forward.

**Verified (live):** `mcstatus` confirmed both the alias and the range
pass-through to Minecraft (MC 26.2, players 0/20). A full `wg-quick
down/up` re-creates the rules idempotently (exactly one DNAT + one MASQ, no
duplicates) and the tunnel re-handshakes.

**Debugging note — inline PostUp is fragile:** appending
`PostUp = iptables -t nat -A ...` (with spaces in the command) after the
`[Peer]` section caused `wg-quick` to fail parsing the config and delete the
interface (`Line unrecognized: PostUp=iptables-tnat-...`). Fixes:

- Place `PostUp`/`PostDown` in the **`[Interface]`** section, not after
  `[Peer]`.
- Prefer a **script path** (`PostUp = /path/to/script.sh`) rather than an
  inline command with many space-separated args.

## 6. Security notes / next steps

- `ONLINE_MODE=false` accepts any offline client — dev lane only.
- Egress to the whole internet is currently allowed (jar bootstrap). Tighten to
  an allow-list of Mojang IPs before production.
- Game edge (UAE relay → WireGuard → NodePort range `30000-30199`) is live,
  persisted, and range-based. For dev, `kubectl port-forward` still exposes
  the server locally.

## 6a. TabListPing plugin (added later)

**Intent:** add only the **TabListPing** plugin so the tab list shows each
player's real ping (ms). It is a Bukkit/Paper plugin, so a **vanilla** server
cannot load it — `TYPE` is switched `VANILLA` → `PAPER`. Nothing else in the
manifests changed (`service.yaml`, `pvc.yaml`, `networkpolicy.yaml` untouched).

Changes in `infra/kubernetes/tenants/minecraft-demo/deployment.yaml`:

- `TYPE: VANILLA` → `TYPE: PAPER` (keeps `VERSION: latest`; image picks the
  latest Paper-supported Minecraft release).
- Added `PLUGINS: https://cdn.modrinth.com/data/MwLGimob/versions/JB16ulew/TabListPing-2.03.jar`
  — the itzg `PLUGINS` var downloads the plugin jar directly into `/data/plugins/`
  on first start, so it persists on the world PVC across pod restarts.
- **Correction:** the first attempt used `MODRINTH_MODS=MwLGimob`, which is
  **not** a real itzg variable — the env var is passed to the container but
  nothing is downloaded. The correct mechanism for individual plugin jars on a
  Paper server is `PLUGINS` (comma/newline list of jar URLs). Also, the server
  runs Paper 26.2 (`VERSION=LATEST`), which requires **TabListPing 2.03**
  (2.02 only supports up to 1.21.11); 2.03 explicitly supports 26.1/26.2.

No egress change needed: the NetworkPolicy already allows outbound internet,
which now also covers the Paper jar + plugin download.

Command:

```bash
python3 -c "import yaml; yaml.safe_load(open('infra/kubernetes/tenants/minecraft-demo/deployment.yaml')); print('deployment.yaml valid')"
# -> deployment.yaml valid
```