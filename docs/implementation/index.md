# Implementation Status — Reference Design

This folder tracks implementation progress against the
[Reference Design](../reference-design/index.md). Each phase/section in the
reference is assigned a status; a generator script renders this page from
`progress.yaml` and the reference tree.

## Legend

| Status | Meaning |
|--------|---------|
| ✅ done | Implemented, verified, and reflected in `infra/` |
| 🔶 in-progress | Actively being implemented |
| ⬜ not-started | Not yet touched |
| ❌ blocked | Blocked on an external dependency |

## How it works

- Source of truth for status: `docs/implementation/progress.yaml`
- Generator: `scripts/docs/docs-generate-implementation.py`
- Regenerate: `python3 scripts/docs/docs-generate-implementation.py`
- The generated output overwrites this `index.md` between markers.

<!-- BEGIN_GENERATED_IMPLEMENTATION -->

## Overall progress

**1 / 92** phases/sections complete (**1%**).

<div style="display:flex;align-items:center;gap:12px;max-width:720px;padding:8px 0;"><div style="flex:1;height:22px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-progress-fill imp-shimmer" style="--imp-w:1.1%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-weight:700;min-width:52px;text-align:right;">1%</div></div>

| Status | Count |
|--------|-------|
| ✅ done | 1 |
| 🔶 in-progress | 0 |
| ⬜ not-started | 91 |
| ❌ blocked | 0 |

## Progress by part

### 3% — Part III — Build the host

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:3.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">3%</div></div><div class="imp-tooltip"><strong>Done (1)</strong>
• Phase 0 — create the infrastructure repository first
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (28)</strong>
• Phase 1 — inventory the actual machine
• Phase 2 — update Ubuntu and install base administration tools
• unattended security updates
• Phase 3 — hostname, DNS, and local identity
• Phase 4 — users, groups, and sudo boundaries
• platform groups
• no shared human account
• sudo policy
• Phase 5 — SSH hardening
• Phase 6 — Tailscale private management path
• Tailscale policy concept
• Phase 7 — host firewall
• Phase 8 — system tuning and resource safety
• disable swap initially
• inotify limits
• basic forwarding
• journald bound
• Phase 9 — developer CPU/RAM/PID limits on the host
• Phase 10 — storage architecture
• desired logical layout
• fresh-install target
• existing-install path
• create dedicated RKE2 filesystem only when backing storage is known
• Kubernetes fast VG
• Kubernetes bulk VG
• required LVM module
• Phase 11 — filesystem quotas for developer homes
• Phase 12 — NVIDIA host driver baseline</div></div>

| Status | Phase |
|--------|-------|
| ✅ `done` | [Phase 0 — create the infrastructure repository first](../reference-design/build/03-build-the-host/00-9-phase-0-create-the-infrastructure-repository-first/index.md) |
| ⬜ `not-started` | [Phase 1 — inventory the actual machine](../reference-design/build/03-build-the-host/01-10-phase-1-inventory-the-actual-machine/index.md) |
| ⬜ `not-started` | [Phase 2 — update Ubuntu and install base administration tools](../reference-design/build/03-build-the-host/02-11-phase-2-update-ubuntu-and-install-base-administration-tools/index.md) |
| ⬜ `not-started` | [unattended security updates](../reference-design/build/03-build-the-host/03-11-1-unattended-security-updates/index.md) |
| ⬜ `not-started` | [Phase 3 — hostname, DNS, and local identity](../reference-design/build/03-build-the-host/04-12-phase-3-hostname-dns-and-local-identity/index.md) |
| ⬜ `not-started` | [Phase 4 — users, groups, and sudo boundaries](../reference-design/build/03-build-the-host/05-13-phase-4-users-groups-and-sudo-boundaries/index.md) |
| ⬜ `not-started` | [platform groups](../reference-design/build/03-build-the-host/06-13-1-platform-groups/index.md) |
| ⬜ `not-started` | [no shared human account](../reference-design/build/03-build-the-host/07-13-2-no-shared-human-account/index.md) |
| ⬜ `not-started` | [sudo policy](../reference-design/build/03-build-the-host/08-13-3-sudo-policy/index.md) |
| ⬜ `not-started` | [Phase 5 — SSH hardening](../reference-design/build/03-build-the-host/09-14-phase-5-ssh-hardening/index.md) |
| ⬜ `not-started` | [Phase 6 — Tailscale private management path](../reference-design/build/03-build-the-host/10-15-phase-6-tailscale-private-management-path/index.md) |
| ⬜ `not-started` | [Tailscale policy concept](../reference-design/build/03-build-the-host/11-15-1-tailscale-policy-concept/index.md) |
| ⬜ `not-started` | [Phase 7 — host firewall](../reference-design/build/03-build-the-host/12-16-phase-7-host-firewall/index.md) |
| ⬜ `not-started` | [Phase 8 — system tuning and resource safety](../reference-design/build/03-build-the-host/13-17-phase-8-system-tuning-and-resource-safety/index.md) |
| ⬜ `not-started` | [disable swap initially](../reference-design/build/03-build-the-host/14-17-1-disable-swap-initially/index.md) |
| ⬜ `not-started` | [inotify limits](../reference-design/build/03-build-the-host/15-17-2-inotify-limits/index.md) |
| ⬜ `not-started` | [basic forwarding](../reference-design/build/03-build-the-host/16-17-3-basic-forwarding/index.md) |
| ⬜ `not-started` | [journald bound](../reference-design/build/03-build-the-host/17-17-4-journald-bound/index.md) |
| ⬜ `not-started` | [Phase 9 — developer CPU/RAM/PID limits on the host](../reference-design/build/03-build-the-host/18-18-phase-9-developer-cpu-ram-pid-limits-on-the-host/index.md) |
| ⬜ `not-started` | [Phase 10 — storage architecture](../reference-design/build/03-build-the-host/19-19-phase-10-storage-architecture/index.md) |
| ⬜ `not-started` | [desired logical layout](../reference-design/build/03-build-the-host/20-19-1-desired-logical-layout/index.md) |
| ⬜ `not-started` | [fresh-install target](../reference-design/build/03-build-the-host/21-19-2-fresh-install-target/index.md) |
| ⬜ `not-started` | [existing-install path](../reference-design/build/03-build-the-host/22-19-3-existing-install-path/index.md) |
| ⬜ `not-started` | [create dedicated RKE2 filesystem only when backing storage is known](../reference-design/build/03-build-the-host/23-19-4-create-dedicated-rke2-filesystem-only-when-backing-storage-is-known/index.md) |
| ⬜ `not-started` | [Kubernetes fast VG](../reference-design/build/03-build-the-host/24-19-5-kubernetes-fast-vg/index.md) |
| ⬜ `not-started` | [Kubernetes bulk VG](../reference-design/build/03-build-the-host/25-19-6-kubernetes-bulk-vg/index.md) |
| ⬜ `not-started` | [required LVM module](../reference-design/build/03-build-the-host/26-19-7-required-lvm-module/index.md) |
| ⬜ `not-started` | [Phase 11 — filesystem quotas for developer homes](../reference-design/build/03-build-the-host/27-20-phase-11-filesystem-quotas-for-developer-homes/index.md) |
| ⬜ `not-started` | [Phase 12 — NVIDIA host driver baseline](../reference-design/build/03-build-the-host/28-21-phase-12-nvidia-host-driver-baseline/index.md) |

### 0% — Part IV — Install RKE2 correctly

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (9)</strong>
• Phase 13 — choose and pin the RKE2 release
• Phase 14 — RKE2 configuration
• kubelet configuration
• Phase 15 — configure RKE2's bundled Cilium
• Phase 16 — install and start RKE2
• inspect Cilium
• verify RKE2 Secrets encryption
• Phase 17 — admin kubeconfig and CLI convenience
• Phase 18 — verify reboot recovery now, not later</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 13 — choose and pin the RKE2 release](../reference-design/build/04-install-rke2-correctly/00-22-phase-13-choose-and-pin-the-rke2-release/index.md) |
| ⬜ `not-started` | [Phase 14 — RKE2 configuration](../reference-design/build/04-install-rke2-correctly/01-23-phase-14-rke2-configuration/index.md) |
| ⬜ `not-started` | [kubelet configuration](../reference-design/build/04-install-rke2-correctly/02-23-1-kubelet-configuration/index.md) |
| ⬜ `not-started` | [Phase 15 — configure RKE2's bundled Cilium](../reference-design/build/04-install-rke2-correctly/03-24-phase-15-configure-rke2-s-bundled-cilium/index.md) |
| ⬜ `not-started` | [Phase 16 — install and start RKE2](../reference-design/build/04-install-rke2-correctly/04-25-phase-16-install-and-start-rke2/index.md) |
| ⬜ `not-started` | [inspect Cilium](../reference-design/build/04-install-rke2-correctly/05-25-1-inspect-cilium/index.md) |
| ⬜ `not-started` | [verify RKE2 Secrets encryption](../reference-design/build/04-install-rke2-correctly/06-25-2-verify-rke2-secrets-encryption/index.md) |
| ⬜ `not-started` | [Phase 17 — admin kubeconfig and CLI convenience](../reference-design/build/04-install-rke2-correctly/07-26-phase-17-admin-kubeconfig-and-cli-convenience/index.md) |
| ⬜ `not-started` | [Phase 18 — verify reboot recovery now, not later](../reference-design/build/04-install-rke2-correctly/08-27-phase-18-verify-reboot-recovery-now-not-later/index.md) |

### 0% — Part V — GitOps bootstrap

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (12)</strong>
• Phase 19 — install Argo CD exactly once by hand
• Phase 20 — root GitOps application
• AppProjects
• Phase 21 — namespace baseline
• Phase 22 — PriorityClasses
• Phase 23 — ResourceQuota
• Phase 24 — LimitRange
• Phase 25 — default-deny NetworkPolicy
• Phase 26 — RBAC
• dev Role
• production is intentionally different
• Phase 27 — authentication for Kubernetes developers</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 19 — install Argo CD exactly once by hand](../reference-design/build/05-gitops-bootstrap/00-28-phase-19-install-argo-cd-exactly-once-by-hand/index.md) |
| ⬜ `not-started` | [Phase 20 — root GitOps application](../reference-design/build/05-gitops-bootstrap/01-29-phase-20-root-gitops-application/index.md) |
| ⬜ `not-started` | [AppProjects](../reference-design/build/05-gitops-bootstrap/02-29-1-appprojects/index.md) |
| ⬜ `not-started` | [Phase 21 — namespace baseline](../reference-design/build/05-gitops-bootstrap/03-30-phase-21-namespace-baseline/index.md) |
| ⬜ `not-started` | [Phase 22 — PriorityClasses](../reference-design/build/05-gitops-bootstrap/04-31-phase-22-priorityclasses/index.md) |
| ⬜ `not-started` | [Phase 23 — ResourceQuota](../reference-design/build/05-gitops-bootstrap/05-32-phase-23-resourcequota/index.md) |
| ⬜ `not-started` | [Phase 24 — LimitRange](../reference-design/build/05-gitops-bootstrap/06-33-phase-24-limitrange/index.md) |
| ⬜ `not-started` | [Phase 25 — default-deny NetworkPolicy](../reference-design/build/05-gitops-bootstrap/07-34-phase-25-default-deny-networkpolicy/index.md) |
| ⬜ `not-started` | [Phase 26 — RBAC](../reference-design/build/05-gitops-bootstrap/08-35-phase-26-rbac/index.md) |
| ⬜ `not-started` | [dev Role](../reference-design/build/05-gitops-bootstrap/09-35-1-dev-role/index.md) |
| ⬜ `not-started` | [production is intentionally different](../reference-design/build/05-gitops-bootstrap/10-35-2-production-is-intentionally-different/index.md) |
| ⬜ `not-started` | [Phase 27 — authentication for Kubernetes developers](../reference-design/build/05-gitops-bootstrap/11-36-phase-27-authentication-for-kubernetes-developers/index.md) |

### 0% — Part VI — Policy enforcement

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 28 — install Kyverno through Argo CD
• Phase 29 — stage policy before enforcing it
• example: deny hostPath
• Phase 30 — policy tests</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 28 — install Kyverno through Argo CD](../reference-design/build/06-policy-enforcement/00-37-phase-28-install-kyverno-through-argo-cd/index.md) |
| ⬜ `not-started` | [Phase 29 — stage policy before enforcing it](../reference-design/build/06-policy-enforcement/01-38-phase-29-stage-policy-before-enforcing-it/index.md) |
| ⬜ `not-started` | [example: deny hostPath](../reference-design/build/06-policy-enforcement/02-38-1-example-deny-hostpath/index.md) |
| ⬜ `not-started` | [Phase 30 — policy tests](../reference-design/build/06-policy-enforcement/03-39-phase-30-policy-tests/index.md) |

### 0% — Part VII — Persistent storage

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 31 — install OpenEBS through Argo CD
• Phase 32 — StorageClasses
• Phase 33 — prove PVC lifecycle before deploying databases</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 31 — install OpenEBS through Argo CD](../reference-design/build/07-persistent-storage/00-40-phase-31-install-openebs-through-argo-cd/index.md) |
| ⬜ `not-started` | [Phase 32 — StorageClasses](../reference-design/build/07-persistent-storage/01-41-phase-32-storageclasses/index.md) |
| ⬜ `not-started` | [Phase 33 — prove PVC lifecycle before deploying databases](../reference-design/build/07-persistent-storage/02-42-phase-33-prove-pvc-lifecycle-before-deploying-databases/index.md) |

### 0% — Part VIII — Monitoring and logs

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 34 — metrics stack
• Phase 35 — logs
• Phase 36 — alert before things are full</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 34 — metrics stack](../reference-design/build/08-monitoring-and-logs/00-43-phase-34-metrics-stack/index.md) |
| ⬜ `not-started` | [Phase 35 — logs](../reference-design/build/08-monitoring-and-logs/01-44-phase-35-logs/index.md) |
| ⬜ `not-started` | [Phase 36 — alert before things are full](../reference-design/build/08-monitoring-and-logs/02-45-phase-36-alert-before-things-are-full/index.md) |

### 0% — Part IX — Registry

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• Phase 37 — install Harbor
• Phase 38 — configure RKE2 registry trust</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 37 — install Harbor](../reference-design/build/09-registry/00-46-phase-37-install-harbor/index.md) |
| ⬜ `not-started` | [Phase 38 — configure RKE2 registry trust](../reference-design/build/09-registry/01-47-phase-38-configure-rke2-registry-trust/index.md) |

### 0% — Part X — Developer build experience

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (7)</strong>
• Phase 39 — alpha does NOT run a developer Docker daemon
• Phase 40 — local developer work on alpha
• Phase 41 — build01 architecture
• Phase 42 — BuildKit cache policy
• Phase 43 — remote BuildKit
• Phase 44 — continuous dev loop
• Phase 45 — CI pipeline</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 39 — alpha does NOT run a developer Docker daemon](../reference-design/build/10-developer-build-experience/00-48-phase-39-alpha-does-not-run-a-developer-docker-daemon/index.md) |
| ⬜ `not-started` | [Phase 40 — local developer work on alpha](../reference-design/build/10-developer-build-experience/01-49-phase-40-local-developer-work-on-alpha/index.md) |
| ⬜ `not-started` | [Phase 41 — build01 architecture](../reference-design/build/10-developer-build-experience/02-50-phase-41-build01-architecture/index.md) |
| ⬜ `not-started` | [Phase 42 — BuildKit cache policy](../reference-design/build/10-developer-build-experience/03-51-phase-42-buildkit-cache-policy/index.md) |
| ⬜ `not-started` | [Phase 43 — remote BuildKit](../reference-design/build/10-developer-build-experience/04-52-phase-43-remote-buildkit/index.md) |
| ⬜ `not-started` | [Phase 44 — continuous dev loop](../reference-design/build/10-developer-build-experience/05-53-phase-44-continuous-dev-loop/index.md) |
| ⬜ `not-started` | [Phase 45 — CI pipeline](../reference-design/build/10-developer-build-experience/06-54-phase-45-ci-pipeline/index.md) |

### 0% — Part XI — Public web path

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 46 — Cloudflare Tunnel
• Phase 47 — public vs private names
• Phase 48 — Traefik routing</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 46 — Cloudflare Tunnel](../reference-design/build/11-public-web-path/00-55-phase-46-cloudflare-tunnel/index.md) |
| ⬜ `not-started` | [Phase 47 — public vs private names](../reference-design/build/11-public-web-path/01-56-phase-47-public-vs-private-names/index.md) |
| ⬜ `not-started` | [Phase 48 — Traefik routing](../reference-design/build/11-public-web-path/02-57-phase-48-traefik-routing/index.md) |

### 0% — Part XII — GPU validation phase

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 49 — GPU integration is optional until proven
• Phase 50 — first GPU goal: whole-GPU scheduling
• Phase 51 — GPU policy
• Phase 52 — HAMi validation</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 49 — GPU integration is optional until proven](../reference-design/build/12-gpu-validation-phase/00-58-phase-49-gpu-integration-is-optional-until-proven/index.md) |
| ⬜ `not-started` | [Phase 50 — first GPU goal: whole-GPU scheduling](../reference-design/build/12-gpu-validation-phase/01-59-phase-50-first-gpu-goal-whole-gpu-scheduling/index.md) |
| ⬜ `not-started` | [Phase 51 — GPU policy](../reference-design/build/12-gpu-validation-phase/02-60-phase-51-gpu-policy/index.md) |
| ⬜ `not-started` | [Phase 52 — HAMi validation](../reference-design/build/12-gpu-validation-phase/03-61-phase-52-hami-validation/index.md) |

### 0% — Part XIII — Game networking foundation

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 53 — keep game workloads in Kubernetes for now
• Phase 54 — why game edge is separate from Cloudflare web
• Phase 55 — relay bring-up</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 53 — keep game workloads in Kubernetes for now](../reference-design/build/13-game-networking-foundation/00-62-phase-53-keep-game-workloads-in-kubernetes-for-now/index.md) |
| ⬜ `not-started` | [Phase 54 — why game edge is separate from Cloudflare web](../reference-design/build/13-game-networking-foundation/01-63-phase-54-why-game-edge-is-separate-from-cloudflare-web/index.md) |
| ⬜ `not-started` | [Phase 55 — relay bring-up](../reference-design/build/13-game-networking-foundation/02-64-phase-55-relay-bring-up/index.md) |

### 0% — Part XIV — Backups and disaster recovery

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 56 — RKE2 etcd snapshots
• Phase 57 — what must be backed up
• Phase 58 — local vs offsite
• Phase 59 — restore tests</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 56 — RKE2 etcd snapshots](../reference-design/build/14-backups-and-disaster-recovery/00-65-phase-56-rke2-etcd-snapshots/index.md) |
| ⬜ `not-started` | [Phase 57 — what must be backed up](../reference-design/build/14-backups-and-disaster-recovery/01-66-phase-57-what-must-be-backed-up/index.md) |
| ⬜ `not-started` | [Phase 58 — local vs offsite](../reference-design/build/14-backups-and-disaster-recovery/02-67-phase-58-local-vs-offsite/index.md) |
| ⬜ `not-started` | [Phase 59 — restore tests](../reference-design/build/14-backups-and-disaster-recovery/03-68-phase-59-restore-tests/index.md) |

### 0% — Part XV — Consolidate and enforce the Ansible source of truth

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (4)</strong>
• Phase 60 — Ansible control environment
• Phase 61 — inventory
• Phase 62 — role ownership
• Phase 63 — Ansible must be idempotent</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 60 — Ansible control environment](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/00-69-phase-60-ansible-control-environment/index.md) |
| ⬜ `not-started` | [Phase 61 — inventory](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/01-70-phase-61-inventory/index.md) |
| ⬜ `not-started` | [Phase 62 — role ownership](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/02-71-phase-62-role-ownership/index.md) |
| ⬜ `not-started` | [Phase 63 — Ansible must be idempotent](../reference-design/build/15-consolidate-and-enforce-the-ansible-source-of-truth/03-72-phase-63-ansible-must-be-idempotent/index.md) |

### 0% — Part XVI — Ubuntu Autoinstall

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 64 — use Autoinstall for future clean rebuilds
• Phase 65 — minimal safe autoinstall skeleton
• Phase 66 — validate Autoinstall in a VM first</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 64 — use Autoinstall for future clean rebuilds](../reference-design/build/16-ubuntu-autoinstall/00-73-phase-64-use-autoinstall-for-future-clean-rebuilds/index.md) |
| ⬜ `not-started` | [Phase 65 — minimal safe autoinstall skeleton](../reference-design/build/16-ubuntu-autoinstall/01-74-phase-65-minimal-safe-autoinstall-skeleton/index.md) |
| ⬜ `not-started` | [Phase 66 — validate Autoinstall in a VM first](../reference-design/build/16-ubuntu-autoinstall/02-75-phase-66-validate-autoinstall-in-a-vm-first/index.md) |

### 0% — Part XVII — OpenTofu for external infrastructure

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• Phase 67 — what OpenTofu should own
• Phase 68 — state is sensitive</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 67 — what OpenTofu should own](../reference-design/build/17-opentofu-for-external-infrastructure/00-76-phase-67-what-opentofu-should-own/index.md) |
| ⬜ `not-started` | [Phase 68 — state is sensitive](../reference-design/build/17-opentofu-for-external-infrastructure/01-77-phase-68-state-is-sensitive/index.md) |

<style>
@keyframes imp-fill { from { width: 0; } to { width: var(--imp-w); } }
@keyframes imp-shimmer { from { background-position: 0 0; } to { background-position: 200% 0; } }
.imp-progress-fill { animation: imp-fill 1.6s cubic-bezier(.22,1,.36,1) forwards; }
.imp-part-fill { animation: imp-fill 1.2s cubic-bezier(.22,1,.36,1) forwards; }
.imp-progress-fill.imp-shimmer { animation: imp-fill 1.6s cubic-bezier(.22,1,.36,1) forwards, imp-shimmer 2s linear infinite; }
.imp-tip { position: relative; }
.imp-tooltip {
  visibility: hidden; opacity: 0; position: absolute; z-index: 30;
  left: 0; top: calc(100% + 8px); width: 320px; max-height: 260px;
  overflow: auto; background: var(--md-default-bg-color);
  color: var(--md-default-fg-color);
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: 8px; box-shadow: 0 6px 24px rgba(0,0,0,.25);
  padding: 10px 12px; font-size: .8em; line-height: 1.5;
  transition: opacity .15s ease, visibility .15s ease; white-space: pre-wrap;
}
.imp-tip:hover .imp-tooltip, .imp-tip:focus-within .imp-tooltip {
  visibility: visible; opacity: 1;
}
</style>

<!-- END_GENERATED_IMPLEMENTATION -->