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

**Verified (live):** a full `wg-quick down wg0 && wg-quick up wg0` re-created
the rules idempotently (exactly one DNAT + one MASQ rule) and the tunnel
re-handshook. External probe confirmed the path end-to-end:

```text
RELAY ONLINE: 26.2 | players 0 / 20   # mcstatus on 89.36.162.171:25565
```

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
- Game edge (UAE relay → WireGuard → NodePort 30079) is live and persisted.
  For dev, `kubectl port-forward` still exposes the server locally.