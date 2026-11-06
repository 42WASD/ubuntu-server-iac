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
`platform-dex`/`platform-kyverno*` `OutOfSync` entries are **not** all
CRD-level drift — see the follow-up below; that original sentence conflated
three different causes and was never actioned.

**Lesson:** an app stuck at `Progressing` with all pods Running on this
platform = check `argocd-config.yaml` health customizations first.

---

# Appendix — clearing the three permanent `OutOfSync` apps (2026-11-06)

The sentence above ("CRD-level server-side-apply drift") was written on
2026-08-24, i.e. **before** `platform-dex` actually broke on 2026-10-14. All
three apps were still `OutOfSync` on 2026-11-06; `refresh=normal` and
`refresh=hard` changed nothing, so this was persistent, not transient cache.
Only **one** of the three was a genuine failure.

Diagnose with the CLI against the in-cluster server:

```bash
kubectl -n argocd port-forward svc/argocd-server 18080:443 >/tmp/pf.log 2>&1 &
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d > /tmp/argo-pw
argocd login localhost:18080 --username admin \
  --password "$(cat /tmp/argo-pw)" --insecure --grpc-web
```

`--plaintext` fails against the 443 forward (`x509: certificate signed by
unknown authority`); use `--insecure` (TLS) with `--grpc-web`.

## 1. `platform-dex` — a real, hard failure

```
Config "" not found (retried 5 times)
operationState.phase = Failed, retryCount = 5, first failed 2026-10-14T10:00:41Z
```

`infra/kubernetes/platform/dex/` is a **directory** source (no
`kustomization.yaml`), so Argo renders *every* `.yaml` in it.
`developer-kubeconfig.template.yaml` is a kubeconfig template, which is valid
YAML with `apiVersion: v1` + `kind: Config` (a kubeconfig kind, not a
Kubernetes resource). Argo tried to apply a nameless `Config` on every sync
and failed. The six real resources (`ConfigMap dex-config`, `Deployment dex`,
`Service dex`, `PersistentVolumeClaim dex-data`, `ServiceAccount dex`,
`IngressRoute dex`) were all `Synced`; dex was `1/1 Running` in namespace
`security` throughout — only the Application object was stuck.

**Fix:** documented skip directive as the first line of that file
(<https://argo-cd.readthedocs.io/en/stable/user-guide/directory/>):

```yaml
# +argocd:skip-file-rendering
```

Renaming to `.yaml.template` also works, but the filename is referenced from
several docs, and the directive states the intent explicitly.

## 2. `platform-kyverno-policies` — Kyverno webhook defaults (false positive)

`kubectl diff` against the kustomize render and `argocd app diff` both showed
nothing, yet all six `ClusterPolicies` reported `OutOfSync`. Structurally
comparing the Argo-desired manifest against the live object showed the only
differences were fields **Kyverno's admission webhook defaults on**:

| path | git | live |
|---|---|---|
| `spec.admission` | absent | `true` |
| `spec.emitWarning` | absent | `false` |
| `spec.rules[].skipBackgroundRequests` | absent | `true` |
| `spec.rules[].validate.allowExistingViolations` | absent | `true` |
| `spec.rules[].validate.cel.generate` | absent | `false` |

**Fix:** `ignoreDifferences` on the Application using `jqPathExpressions`
with `rules[]` wildcards, because rule counts differ per policy (5 for
`disallow-privileged-host-settings`, 1 for `require-resource-limits`).

## 3. `platform-kyverno` — Helm chart renders empty maps (false positive)

```
===== apiextensions.k8s.io/CustomResourceDefinition /validatingpolicies.policies.kyverno.io ======
4a5
>   labels: {}
```

A full structural diff of the chart-rendered CRD vs live found exactly:

```
ONLY-GIT  .metadata.annotations = {}
ONLY-GIT  .metadata.labels = {}
ONLY-LIVE .spec.conversion = {"strategy": "None"}
(+ server-managed creationTimestamp/generation/resourceVersion/uid/status)
```

The chart emits empty maps; the apiserver stores the keys absent and defaults
`spec.conversion`. The 12th non-synced resource is
`Job platform-kyverno-migrate-resources`, a Helm `post-upgrade` hook
(`helm.sh/hook: post-upgrade`): absent from the rendered manifests, and
completed Jobs are immutable, so it can never be marked `Synced`.

**Fix:** `ignoreDifferences` for those CRD paths and the hook Job's status.

## Commands run

```bash
kubectl apply \
  -f infra/kubernetes/bootstrap/argocd/apps/platform-kyverno.yaml \
  -f infra/kubernetes/bootstrap/argocd/apps/platform-kyverno-policies.yaml

kubectl get applications -n argocd \
  -o custom-columns='NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status'
```

**Verified (live):**

```
platform-kyverno            Synced   Healthy
platform-kyverno-policies   Synced   Healthy
platform-dex                OutOfSync Healthy   # until the skip-file commit is pushed
```

`platform-dex` clears once the `# +argocd:skip-file-rendering` change is
pushed — Argo reads the git remote, not the working tree.

## Lessons

- `OutOfSync` needs a per-app `argocd app diff`, not one shared explanation.
  Two of these were cosmetic; one was a hard sync failure hidden behind the
  same status string.
- A `directory`-type source renders **every** `.yaml`/`.yml`/`.json` in the
  directory. Templates, values files, and kubeconfigs that happen to be valid
  YAML with `apiVersion`/`kind` will be applied. Use
  `# +argocd:skip-file-rendering` or `spec.source.directory.exclude`.
- `argocd app diff` printing nothing while the app stays `OutOfSync` means a
  diff-normalization/`ignoreDifferences` mismatch; compare the desired
  manifest against the live object structurally to find the real path.
- Prefer `jqPathExpressions` with `[]` wildcards for arrays whose length
  varies between objects.
