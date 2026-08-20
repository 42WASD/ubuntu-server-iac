---
phase: 11-public-web-path/00-55-phase-46-cloudflare-tunnel
---
# Phase 46 — Cloudflare Tunnel

Deployed `cloudflared` in-cluster through Argo CD to connect the platform to
Cloudflare's edge via an outbound tunnel, with no inbound home ports opened.
The tunnel token is a credential and is stored in a Kubernetes Secret in the
cluster — never committed to Git.

## 46.1 What was deployed

`infra/kubernetes/platform/cloudflared/deployment.yaml`:

- A `Deployment` named `cloudflared` in the `ingress` namespace.
- Image pinned `cloudflare/cloudflared:2026.8.2`.
- Runs `tunnel run --protocol http2 --token "$(TUNNEL_TOKEN)"`.
- `TUNNEL_TOKEN` is read from the `cloudflared-token` Secret (`ingress` ns) via
  `secretKeyRef` — the literal never appears in Git.
- Named `metrics` port `20241`; `startupProbe` + `livenessProbe` on
  `GET /ready` (the metrics port).
- `--protocol http2` is forced because outbound QUIC/UDP (port 7844) times out
  on this network; cloudflared otherwise stays in a retry loop and never
  registers. HTTP/2 over TCP 443 is fully functional.

Argo child app `infra/kubernetes/bootstrap/argocd/apps/platform-cloudflared.yaml`
(`platform-cloudflared`, sync-wave `-4`) applies the manifest path
`infra/kubernetes/platform/cloudflared` and is auto-discovered by
`platform-root`.

## 46.2 Commands run

Create the token Secret in the cluster (value applied verbatim from a temp
file, not retyped, then removed):

```bash
kubectl -n ingress create secret generic cloudflared-token \
  --from-file=token=/tmp/cftoken --dry-run=client -o yaml | kubectl apply -f -
rm -f /tmp/cftoken
```

Sync the new child app via the root app, then sync the app itself:

```bash
kubectl -n argocd patch application platform-root \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
kubectl -n argocd patch application platform-cloudflared \
  --type merge -p '{"operation":{"sync":{"syncStrategy":{"apply":{"force":true}}}}}'
```

## 46.3 Verification

```bash
kubectl -n ingress get pods -l app=cloudflared          # 1/1 Running
kubectl -n ingress get deploy cloudflared               # 1/1 Available
kubectl -n argocd get app platform-cloudflared          # Synced  Healthy
kubectl -n ingress logs <cloudflared-pod> \
  | grep "Registered tunnel connection"                 # 4 x connIndex, protocol=http2
```

Logged `Registered tunnel connection` for all four HA connections
(`connIndex=0..3`) over `protocol=http2`. The `UDP Connectivity FAIL / QUIC`
lines are informational only — QUIC/UDP is blocked on this network and
`--protocol http2` forces the TCP/443 path.

## 46.4 Notes / issues

- A hand-typed token transcription caused an initial `CrashLoopBackOff` with
  `Provided Tunnel token is not valid`. Fix: load the token into the Secret
  verbatim from a file, never retype it.
- The first liveness probe pointed at `/ready` on port `2000` (nothing listens
  there) — the container was killed every 10s. Correct port is `20241`
  (the metrics/health port).
- Public hostname(s) and origin routing to Traefik are configured in the
  Cloudflare dashboard / Phase 48. Phase 46 only connects the edge to the
  cluster.