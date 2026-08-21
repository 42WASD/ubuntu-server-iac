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
| `service.yaml` | ClusterIP Service :25565 (game edge = UAE relay -> WireGuard) |
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
- **ClusterIP not NodePort/LB**: the game edge is the UAE relay → WireGuard →
  ClusterIP (Phase 54). Also avoids the Kyverno
  `restrict-exposure-and-image-tags` NodePort/LoadBalancer flags. Reach via
  `kubectl port-forward` in dev.
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

## 6. Security notes / next steps

- `ONLINE_MODE=false` accepts any offline client — dev lane only.
- Egress to the whole internet is currently allowed (jar bootstrap). Tighten to
  an allow-list of Mojang IPs before production.
- Game edge (UAE relay → WireGuard → ClusterIP) is Phase 55 wiring; for dev,
  `kubectl port-forward` exposes the server.