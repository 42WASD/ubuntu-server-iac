---
phase: 05-gitops-bootstrap/root-gitops-application/argocd-instance-config
---

# Appendix — Argo CD instance config: Ingress health check (2026-08-29)

**Problem:** the `tenant-community-web` Application (and any app with a plain
`networking.k8s.io/Ingress`) sat at **Synced / Progressing** forever. Argo's
built-in Ingress health only covers the deprecated `extensions/v1beta1`
kind, and this cluster's on-prem Traefik never populates
`status.loadBalancer` — so the common LB-based check never resolves.

**Fix:** `infra/kubernetes/bootstrap/argocd/argocd-config.yaml` — the SSOT
for hand-applied Argo CD instance configuration (Argo bootstraps itself
outside GitOps, Phase 19). Adds a spec-based
`resource.customizations.health.networking.k8s.io_Ingress`: Healthy when the
Ingress has rules (Traefik programs the router at that point; live-verified
that both `wasd.42base.com` and `meme.alpha.taild82ced.ts.net` serve 200
with empty LB status).

```bash
# apply (merge single key — the cm carries stock ignoreResourceUpdates keys)
python3 - <<'PY'
import subprocess, json, yaml
doc = yaml.safe_load(open("infra/kubernetes/bootstrap/argocd/argocd-config.yaml"))
key = "resource.customizations.health.networking.k8s.io_Ingress"
patch = {"data": {key: doc["data"][key]}}
print(subprocess.run(["kubectl", "-n", "argocd", "patch", "configmap",
      "argocd-cm", "--type", "merge", "-p", json.dumps(patch)],
      capture_output=True, text=True).stdout)
PY
# reload + refresh
kubectl -n argocd rollout restart deployment/argocd-server \
  statefulset/argocd-application-controller
kubectl -n argocd patch application tenant-community-web --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

**Verified (live):** all 16 Applications now `Healthy` — including
`tenant-community-web` (previously the only `Progressing`). The three
`platform-dex`/`platform-kyverno*` `OutOfSync` entries are CRD-level
server-side-apply drift; all pods Running.

**Lesson:** an app stuck at `Progressing` with all pods Running on this
platform = check `argocd-config.yaml` health customizations first.
