# Argo CD instance configuration

Argo CD installs itself once by hand (the bootstrap paradox — see
`install-argo-cd-exactly-once-by-hand`), so its **own** ConfigMap
(`argocd-cm`) lives outside the GitOps loop. Deliberate customizations on
top of the stock install are recorded in the SSOT at
`infra/kubernetes/bootstrap/argocd/argocd-config.yaml` and applied by hand
with a single-key merge (the live ConfigMap also carries stock
`ignoreResourceUpdates` keys that must not be clobbered).

## Ingress health check

**Why:** an Application whose tree contains a plain
`networking.k8s.io/Ingress` (e.g. `tenant-community-web`) sat at
**Synced / Progressing** forever. The built-in Ingress health only covers
the deprecated `extensions/v1beta1` kind, and this cluster's on-prem
Traefik never populates `status.loadBalancer` — so the common LB-based Lua
check never resolves either.

**What:** a spec-based
`resource.customizations.health.networking.k8s.io_Ingress` — Healthy when
the Ingress has rules. Traefik programs the router as soon as the Ingress
exists; live-verified that both `wasd.42base.com` and
`meme.alpha.taild82ced.ts.net` serve 200 with an empty LB status.

## Apply

```bash
# from the repo root — merge ONLY the new key into the live cm
python3 - <<'PY'
import subprocess, json, yaml
doc = yaml.safe_load(open("infra/kubernetes/bootstrap/argocd/argocd-config.yaml"))
key = "resource.customizations.health.networking.k8s.io_Ingress"
patch = {"data": {key: doc["data"][key]}}
print(subprocess.run(["kubectl", "-n", "argocd", "patch", "configmap",
      "argocd-cm", "--type", "merge", "-p", json.dumps(patch)],
      capture_output=True, text=True).stdout)
PY

# reload the components that evaluate health, then hard-refresh the app
kubectl -n argocd rollout restart deployment/argocd-server \
  statefulset/argocd-application-controller
kubectl -n argocd patch application tenant-community-web --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

## Verify

```bash
kubectl -n argocd get applications \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status
```

Expected: every Application `Healthy` (verified 2026-08-29 —
`tenant-community-web` was the only `Progressing` before this change).

## Diagnostic rule of thumb

An app stuck at `Progressing` with all pods Running on this platform =
check the health customizations in `argocd-config.yaml` first, not the
workload.
