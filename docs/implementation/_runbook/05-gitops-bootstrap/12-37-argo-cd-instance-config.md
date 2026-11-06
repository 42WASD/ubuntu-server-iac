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

---

# Appendix — changing an immutable-ish field under Server-Side Apply (2026-11-06)

**Problem:** switching the `security/dex` Deployment from `RollingUpdate` to
`Recreate` could not be applied by Argo, and the sync retried forever:

```text
Deployment.apps "dex" is invalid: spec.strategy.rollingUpdate: Forbidden:
may not be specified when strategy `type` is 'Recreate'
```

`kubectl apply --dry-run=server` of the same manifest **succeeded**, and a
manual `kubectl replace`-style change worked. So the manifest was valid and the
cluster was healthy — only *Argo's* apply path was stuck.

## Root cause: SSA deletion is ownership-gated

The Application runs `ServerSideApply=true`. Asking for `Recreate` requires
**deleting** `spec.strategy.rollingUpdate`. Under Server-Side Apply a field can
only be removed by a manager that *already owns it*. `managedFields` showed it
did not:

```bash
kubectl -n security get deploy dex -o json --show-managed-fields \
| python3 -c '
import sys, json
d = json.load(sys.stdin)
for mf in d["metadata"]["managedFields"]:
    fv = mf.get("fieldsV1", {}).get("f:spec", {})
    if fv:
        print(mf["manager"], mf["operation"], "owns spec.strategy:", "f:strategy" in fv)
'
```

```text
argocd-controller   Apply   owns spec.strategy: False
kubectl-rollout     Update  owns spec.strategy: False
```

So applying

```yaml
strategy:
  type: Recreate
  rollingUpdate: null
```

did exactly half the job: SSA **gained** ownership of the leaf it set
(`type: Recreate`) but **could not delete** a field it never owned, leaving the
invalid pair `Recreate + rollingUpdate`. Kubernetes rejects the object, the sync
fails, and Argo retries in a loop.

> **Key misconception to unlearn:** `field: null` in a manifest does **not**
> mean "remove this field" to Server-Side Apply. Deletion is gated on
> ownership, not on the value you send. This is the single most common reason a
> "just set it to null" fix silently does nothing under `ServerSideApply=true`.

## The standard fix: `Replace=true`

Argo CD's documented escape hatch. `Replace=true` makes Argo use
`kubectl replace` / `kubectl create` (a full-object PUT) instead of a patch, so
field ownership stops mattering and fields absent from the manifest are truly
gone.

Set it on the **one resource** that needs it, as an annotation:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-options: Replace=true
```

It can also be set app-wide (`spec.syncPolicy.syncOptions`), but that is the
wrong default here — see "Choosing the option" below.

### Why per-resource and not Application-wide

| Option | Scope in this repo | Verdict |
|---|---|---|
| `Replace=true` **on the resource** | only `dex` | **chosen** |
| `Replace=true` app-wide | every resource in `platform-dex` | too blunt — discards partial-apply semantics everywhere |
| `Force=true,Replace=true` | n/a | **rejected**: delete + recreate the Deployment = real outage |
| `ServerSideApply=false` app-wide | every resource | rejected — gives up SSA for one bad field |
| `kubectl delete` the Deployment to "reset" ownership | n/a | works, but leaves live state diverged from Git and is not reproducible |

`Replace` rewrites the object in place; `Force` deletes and recreates it. For a
PVC-backed single-writer database that is the difference between a rollout and
an outage.

## Choosing the option — decision order

When Argo cannot converge a field, work down this list. Stop at the first that
is genuinely correct; do not reach for the destructive ones to make a red
status go green.

1. **Is the live object wrong, or is Git wrong?** Fix Git if Git is wrong.
   Hand-patching live is never the fix — `selfHeal: true` will revert it (see
   below).
2. **`ignoreDifferences` / `RespectIgnoreDifferences`** — when the field is
   *legitimately* set by a controller or webhook (Kyverno defaulting, CRD
   conversion, HPA-owned `replicas`). This is a *comparison* fix and changes
   nothing live.
3. **`Replace=true` (per-resource)** — when you must remove/patch a field you do
   not own. Ownership-agnostic, in-place, non-destructive.
4. **Recreate the object** (delete + let Argo re-create) — resets ownership
   entirely. Acceptable for stateless objects; verify PVCs/state first.
5. **`Force=true`** — last resort, only where a brief absence is harmless.

Also relevant and used elsewhere in this repo: `Prune=false`,
`Prune=confirm`, `Delete=false`, `SkipDryRunOnMissingResource=true`,
`ApplyOutOfSyncOnly=true`.

## Second half of the bug: RWO means one *mount*, not one pod

`Recreate` was not cosmetic. `dex` owns a `ReadWriteOnce` PVC, and on this
cluster (OpenEBS local-LVM) RWO means **one mount**, not "one pod per node". The
default `RollingUpdate` with `replicas: 1` computes:

```text
maxUnavailable: 25%  ->  0.25 replicas  ->  rounds DOWN to 0
```

Zero pods may be unavailable, so the scheduler starts the replacement while the
old pod still holds the volume, and the mount is refused:

```text
MountVolume.SetUp failed for volume "pvc-f2c681c5-..." :
rpc error: code = Internal desc = verifyMount: device already mounted at
[/var/lib/kubelet/pods/4d84eea2-.../volumes/kubernetes.io~csi/pvc-f2c681c5-.../mount]
```

The new pod hangs in `ContainerCreating`, the old one keeps crash-looping, and
the rollout deadlocks at `Progressing` — **two** pods, neither serving. This is
the same failure already recorded for ATM10SKY in the games repo.

`Recreate` is the only correct strategy for any single-writer workload on RWO
storage (SQLite, a Minecraft world dir, a database data dir). It is also the
semantically correct choice: two `dex` processes must never open the same
`dex.db`.

## What NOT to do — `kubectl` live against an auto-synced app

While debugging this, manifests were applied live before being committed. The
Application runs `automated: {prune: true, selfHeal: true}`, so Argo reconciled
back to the last commit and **pruned** the new objects within ~60 s:

```text
OperationStarted: Initiated automated sync to '62f4f863993d...'
Partial sync operation succeeded
```

```text
$ kubectl -n prd-games-42wasd-admin get svc mc-router
Error from server (NotFound): services "mc-router" not found
```

A live `kubectl apply` against a self-healing Application is a *temporary*
state, not a deployment. Commit → push → let Argo apply (or trigger a sync).
This is the same class of surprise as `platform-root` reverting hand-patched
Application objects.

Corollary: when a NodePort moves between Services, the ports are **exclusively
allocated**, and Argo may apply them in an unlucky order:

```text
Service "mc-router" is invalid: spec.ports[0].nodePort: Invalid value:
30079: provided port is already allocated
```

That is transient — the second sync succeeds once the old owner is gone. Do not
"fix" it by picking a random new port.

## Preparation: check ownership before you fight a sync

```bash
# who owns the field Argo refuses to change?
kubectl -n <ns> get <kind> <name> -o json --show-managed-fields \
| python3 -c '
import sys, json
d = json.load(sys.stdin)
for mf in d["metadata"]["managedFields"]:
    keys = list(mf.get("fieldsV1", {}).keys())
    print(mf["manager"], "|", mf["operation"], "|", keys[:5])
'
```

If `argocd-controller` with `op=Apply` does not list the field you are trying to
remove, `ServerSideApply` cannot do it and you need `Replace=true`.
