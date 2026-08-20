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

**1 / 170** phases/sections complete (**1%**).

<div style="display:flex;align-items:center;gap:12px;max-width:720px;padding:8px 0;"><div style="flex:1;height:22px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-progress-fill imp-shimmer" style="--imp-w:0.6%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-weight:700;min-width:52px;text-align:right;">1%</div></div>

| Status | Count |
|--------|-------|
| ✅ done | 1 |
| 🔶 in-progress | 0 |
| ⬜ not-started | 169 |
| ❌ blocked | 0 |

## Progress by part

### 0% — Part I — Understand the platform before installing anything

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (11)</strong>
• The one-sentence idea
• The target architecture
• The trust model
• What each developer is allowed to do
• Five control planes, not one
• Linux control plane
• Kubernetes platform control plane
• Tenant application control plane
• Build control plane
• External edge control plane
• Why this guide is phased</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [The one-sentence idea](../reference-design/01-understand-the-platform-before-installing-anything/00-0-the-one-sentence-idea/index.md) |
| ⬜ `not-started` | [The target architecture](../reference-design/01-understand-the-platform-before-installing-anything/01-1-the-target-architecture/index.md) |
| ⬜ `not-started` | [The trust model](../reference-design/01-understand-the-platform-before-installing-anything/02-2-the-trust-model/index.md) |
| ⬜ `not-started` | [What each developer is allowed to do](../reference-design/01-understand-the-platform-before-installing-anything/03-3-what-each-developer-is-allowed-to-do/index.md) |
| ⬜ `not-started` | [Five control planes, not one](../reference-design/01-understand-the-platform-before-installing-anything/04-4-five-control-planes-not-one/index.md) |
| ⬜ `not-started` | [Linux control plane](../reference-design/01-understand-the-platform-before-installing-anything/05-4-1-linux-control-plane/index.md) |
| ⬜ `not-started` | [Kubernetes platform control plane](../reference-design/01-understand-the-platform-before-installing-anything/06-4-2-kubernetes-platform-control-plane/index.md) |
| ⬜ `not-started` | [Tenant application control plane](../reference-design/01-understand-the-platform-before-installing-anything/07-4-3-tenant-application-control-plane/index.md) |
| ⬜ `not-started` | [Build control plane](../reference-design/01-understand-the-platform-before-installing-anything/08-4-4-build-control-plane/index.md) |
| ⬜ `not-started` | [External edge control plane](../reference-design/01-understand-the-platform-before-installing-anything/09-4-5-external-edge-control-plane/index.md) |
| ⬜ `not-started` | [Why this guide is phased](../reference-design/01-understand-the-platform-before-installing-anything/10-5-why-this-guide-is-phased/index.md) |

### 0% — Part II — Verified stack and current caveats

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Stack selection
• Current verification caveats — read before installing
• Version policy</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Stack selection](../reference-design/02-verified-stack-and-current-caveats/00-6-stack-selection/index.md) |
| ⬜ `not-started` | [Current verification caveats — read before installing](../reference-design/02-verified-stack-and-current-caveats/01-7-current-verification-caveats-read-before-installing/index.md) |
| ⬜ `not-started` | [Version policy](../reference-design/02-verified-stack-and-current-caveats/02-8-version-policy/index.md) |

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
| ✅ `done` | [Phase 0 — create the infrastructure repository first](../reference-design/03-build-the-host/00-9-phase-0-create-the-infrastructure-repository-first/index.md) |
| ⬜ `not-started` | [Phase 1 — inventory the actual machine](../reference-design/03-build-the-host/01-10-phase-1-inventory-the-actual-machine/index.md) |
| ⬜ `not-started` | [Phase 2 — update Ubuntu and install base administration tools](../reference-design/03-build-the-host/02-11-phase-2-update-ubuntu-and-install-base-administration-tools/index.md) |
| ⬜ `not-started` | [unattended security updates](../reference-design/03-build-the-host/03-11-1-unattended-security-updates/index.md) |
| ⬜ `not-started` | [Phase 3 — hostname, DNS, and local identity](../reference-design/03-build-the-host/04-12-phase-3-hostname-dns-and-local-identity/index.md) |
| ⬜ `not-started` | [Phase 4 — users, groups, and sudo boundaries](../reference-design/03-build-the-host/05-13-phase-4-users-groups-and-sudo-boundaries/index.md) |
| ⬜ `not-started` | [platform groups](../reference-design/03-build-the-host/06-13-1-platform-groups/index.md) |
| ⬜ `not-started` | [no shared human account](../reference-design/03-build-the-host/07-13-2-no-shared-human-account/index.md) |
| ⬜ `not-started` | [sudo policy](../reference-design/03-build-the-host/08-13-3-sudo-policy/index.md) |
| ⬜ `not-started` | [Phase 5 — SSH hardening](../reference-design/03-build-the-host/09-14-phase-5-ssh-hardening/index.md) |
| ⬜ `not-started` | [Phase 6 — Tailscale private management path](../reference-design/03-build-the-host/10-15-phase-6-tailscale-private-management-path/index.md) |
| ⬜ `not-started` | [Tailscale policy concept](../reference-design/03-build-the-host/11-15-1-tailscale-policy-concept/index.md) |
| ⬜ `not-started` | [Phase 7 — host firewall](../reference-design/03-build-the-host/12-16-phase-7-host-firewall/index.md) |
| ⬜ `not-started` | [Phase 8 — system tuning and resource safety](../reference-design/03-build-the-host/13-17-phase-8-system-tuning-and-resource-safety/index.md) |
| ⬜ `not-started` | [disable swap initially](../reference-design/03-build-the-host/14-17-1-disable-swap-initially/index.md) |
| ⬜ `not-started` | [inotify limits](../reference-design/03-build-the-host/15-17-2-inotify-limits/index.md) |
| ⬜ `not-started` | [basic forwarding](../reference-design/03-build-the-host/16-17-3-basic-forwarding/index.md) |
| ⬜ `not-started` | [journald bound](../reference-design/03-build-the-host/17-17-4-journald-bound/index.md) |
| ⬜ `not-started` | [Phase 9 — developer CPU/RAM/PID limits on the host](../reference-design/03-build-the-host/18-18-phase-9-developer-cpu-ram-pid-limits-on-the-host/index.md) |
| ⬜ `not-started` | [Phase 10 — storage architecture](../reference-design/03-build-the-host/19-19-phase-10-storage-architecture/index.md) |
| ⬜ `not-started` | [desired logical layout](../reference-design/03-build-the-host/20-19-1-desired-logical-layout/index.md) |
| ⬜ `not-started` | [fresh-install target](../reference-design/03-build-the-host/21-19-2-fresh-install-target/index.md) |
| ⬜ `not-started` | [existing-install path](../reference-design/03-build-the-host/22-19-3-existing-install-path/index.md) |
| ⬜ `not-started` | [create dedicated RKE2 filesystem only when backing storage is known](../reference-design/03-build-the-host/23-19-4-create-dedicated-rke2-filesystem-only-when-backing-storage-is-known/index.md) |
| ⬜ `not-started` | [Kubernetes fast VG](../reference-design/03-build-the-host/24-19-5-kubernetes-fast-vg/index.md) |
| ⬜ `not-started` | [Kubernetes bulk VG](../reference-design/03-build-the-host/25-19-6-kubernetes-bulk-vg/index.md) |
| ⬜ `not-started` | [required LVM module](../reference-design/03-build-the-host/26-19-7-required-lvm-module/index.md) |
| ⬜ `not-started` | [Phase 11 — filesystem quotas for developer homes](../reference-design/03-build-the-host/27-20-phase-11-filesystem-quotas-for-developer-homes/index.md) |
| ⬜ `not-started` | [Phase 12 — NVIDIA host driver baseline](../reference-design/03-build-the-host/28-21-phase-12-nvidia-host-driver-baseline/index.md) |

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
| ⬜ `not-started` | [Phase 13 — choose and pin the RKE2 release](../reference-design/04-install-rke2-correctly/00-22-phase-13-choose-and-pin-the-rke2-release/index.md) |
| ⬜ `not-started` | [Phase 14 — RKE2 configuration](../reference-design/04-install-rke2-correctly/01-23-phase-14-rke2-configuration/index.md) |
| ⬜ `not-started` | [kubelet configuration](../reference-design/04-install-rke2-correctly/02-23-1-kubelet-configuration/index.md) |
| ⬜ `not-started` | [Phase 15 — configure RKE2's bundled Cilium](../reference-design/04-install-rke2-correctly/03-24-phase-15-configure-rke2-s-bundled-cilium/index.md) |
| ⬜ `not-started` | [Phase 16 — install and start RKE2](../reference-design/04-install-rke2-correctly/04-25-phase-16-install-and-start-rke2/index.md) |
| ⬜ `not-started` | [inspect Cilium](../reference-design/04-install-rke2-correctly/05-25-1-inspect-cilium/index.md) |
| ⬜ `not-started` | [verify RKE2 Secrets encryption](../reference-design/04-install-rke2-correctly/06-25-2-verify-rke2-secrets-encryption/index.md) |
| ⬜ `not-started` | [Phase 17 — admin kubeconfig and CLI convenience](../reference-design/04-install-rke2-correctly/07-26-phase-17-admin-kubeconfig-and-cli-convenience/index.md) |
| ⬜ `not-started` | [Phase 18 — verify reboot recovery now, not later](../reference-design/04-install-rke2-correctly/08-27-phase-18-verify-reboot-recovery-now-not-later/index.md) |

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
| ⬜ `not-started` | [Phase 19 — install Argo CD exactly once by hand](../reference-design/05-gitops-bootstrap/00-28-phase-19-install-argo-cd-exactly-once-by-hand/index.md) |
| ⬜ `not-started` | [Phase 20 — root GitOps application](../reference-design/05-gitops-bootstrap/01-29-phase-20-root-gitops-application/index.md) |
| ⬜ `not-started` | [AppProjects](../reference-design/05-gitops-bootstrap/02-29-1-appprojects/index.md) |
| ⬜ `not-started` | [Phase 21 — namespace baseline](../reference-design/05-gitops-bootstrap/03-30-phase-21-namespace-baseline/index.md) |
| ⬜ `not-started` | [Phase 22 — PriorityClasses](../reference-design/05-gitops-bootstrap/04-31-phase-22-priorityclasses/index.md) |
| ⬜ `not-started` | [Phase 23 — ResourceQuota](../reference-design/05-gitops-bootstrap/05-32-phase-23-resourcequota/index.md) |
| ⬜ `not-started` | [Phase 24 — LimitRange](../reference-design/05-gitops-bootstrap/06-33-phase-24-limitrange/index.md) |
| ⬜ `not-started` | [Phase 25 — default-deny NetworkPolicy](../reference-design/05-gitops-bootstrap/07-34-phase-25-default-deny-networkpolicy/index.md) |
| ⬜ `not-started` | [Phase 26 — RBAC](../reference-design/05-gitops-bootstrap/08-35-phase-26-rbac/index.md) |
| ⬜ `not-started` | [dev Role](../reference-design/05-gitops-bootstrap/09-35-1-dev-role/index.md) |
| ⬜ `not-started` | [production is intentionally different](../reference-design/05-gitops-bootstrap/10-35-2-production-is-intentionally-different/index.md) |
| ⬜ `not-started` | [Phase 27 — authentication for Kubernetes developers](../reference-design/05-gitops-bootstrap/11-36-phase-27-authentication-for-kubernetes-developers/index.md) |

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
| ⬜ `not-started` | [Phase 28 — install Kyverno through Argo CD](../reference-design/06-policy-enforcement/00-37-phase-28-install-kyverno-through-argo-cd/index.md) |
| ⬜ `not-started` | [Phase 29 — stage policy before enforcing it](../reference-design/06-policy-enforcement/01-38-phase-29-stage-policy-before-enforcing-it/index.md) |
| ⬜ `not-started` | [example: deny hostPath](../reference-design/06-policy-enforcement/02-38-1-example-deny-hostpath/index.md) |
| ⬜ `not-started` | [Phase 30 — policy tests](../reference-design/06-policy-enforcement/03-39-phase-30-policy-tests/index.md) |

### 0% — Part VII — Persistent storage

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 31 — install OpenEBS through Argo CD
• Phase 32 — StorageClasses
• Phase 33 — prove PVC lifecycle before deploying databases</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 31 — install OpenEBS through Argo CD](../reference-design/07-persistent-storage/00-40-phase-31-install-openebs-through-argo-cd/index.md) |
| ⬜ `not-started` | [Phase 32 — StorageClasses](../reference-design/07-persistent-storage/01-41-phase-32-storageclasses/index.md) |
| ⬜ `not-started` | [Phase 33 — prove PVC lifecycle before deploying databases](../reference-design/07-persistent-storage/02-42-phase-33-prove-pvc-lifecycle-before-deploying-databases/index.md) |

### 0% — Part VIII — Monitoring and logs

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 34 — metrics stack
• Phase 35 — logs
• Phase 36 — alert before things are full</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 34 — metrics stack](../reference-design/08-monitoring-and-logs/00-43-phase-34-metrics-stack/index.md) |
| ⬜ `not-started` | [Phase 35 — logs](../reference-design/08-monitoring-and-logs/01-44-phase-35-logs/index.md) |
| ⬜ `not-started` | [Phase 36 — alert before things are full](../reference-design/08-monitoring-and-logs/02-45-phase-36-alert-before-things-are-full/index.md) |

### 0% — Part IX — Registry

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• Phase 37 — install Harbor
• Phase 38 — configure RKE2 registry trust</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 37 — install Harbor](../reference-design/09-registry/00-46-phase-37-install-harbor/index.md) |
| ⬜ `not-started` | [Phase 38 — configure RKE2 registry trust](../reference-design/09-registry/01-47-phase-38-configure-rke2-registry-trust/index.md) |

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
| ⬜ `not-started` | [Phase 39 — alpha does NOT run a developer Docker daemon](../reference-design/10-developer-build-experience/00-48-phase-39-alpha-does-not-run-a-developer-docker-daemon/index.md) |
| ⬜ `not-started` | [Phase 40 — local developer work on alpha](../reference-design/10-developer-build-experience/01-49-phase-40-local-developer-work-on-alpha/index.md) |
| ⬜ `not-started` | [Phase 41 — build01 architecture](../reference-design/10-developer-build-experience/02-50-phase-41-build01-architecture/index.md) |
| ⬜ `not-started` | [Phase 42 — BuildKit cache policy](../reference-design/10-developer-build-experience/03-51-phase-42-buildkit-cache-policy/index.md) |
| ⬜ `not-started` | [Phase 43 — remote BuildKit](../reference-design/10-developer-build-experience/04-52-phase-43-remote-buildkit/index.md) |
| ⬜ `not-started` | [Phase 44 — continuous dev loop](../reference-design/10-developer-build-experience/05-53-phase-44-continuous-dev-loop/index.md) |
| ⬜ `not-started` | [Phase 45 — CI pipeline](../reference-design/10-developer-build-experience/06-54-phase-45-ci-pipeline/index.md) |

### 0% — Part XI — Public web path

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 46 — Cloudflare Tunnel
• Phase 47 — public vs private names
• Phase 48 — Traefik routing</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 46 — Cloudflare Tunnel](../reference-design/11-public-web-path/00-55-phase-46-cloudflare-tunnel/index.md) |
| ⬜ `not-started` | [Phase 47 — public vs private names](../reference-design/11-public-web-path/01-56-phase-47-public-vs-private-names/index.md) |
| ⬜ `not-started` | [Phase 48 — Traefik routing](../reference-design/11-public-web-path/02-57-phase-48-traefik-routing/index.md) |

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
| ⬜ `not-started` | [Phase 49 — GPU integration is optional until proven](../reference-design/12-gpu-validation-phase/00-58-phase-49-gpu-integration-is-optional-until-proven/index.md) |
| ⬜ `not-started` | [Phase 50 — first GPU goal: whole-GPU scheduling](../reference-design/12-gpu-validation-phase/01-59-phase-50-first-gpu-goal-whole-gpu-scheduling/index.md) |
| ⬜ `not-started` | [Phase 51 — GPU policy](../reference-design/12-gpu-validation-phase/02-60-phase-51-gpu-policy/index.md) |
| ⬜ `not-started` | [Phase 52 — HAMi validation](../reference-design/12-gpu-validation-phase/03-61-phase-52-hami-validation/index.md) |

### 0% — Part XIII — Game networking foundation

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 53 — keep game workloads in Kubernetes for now
• Phase 54 — why game edge is separate from Cloudflare web
• Phase 55 — relay bring-up</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 53 — keep game workloads in Kubernetes for now](../reference-design/13-game-networking-foundation/00-62-phase-53-keep-game-workloads-in-kubernetes-for-now/index.md) |
| ⬜ `not-started` | [Phase 54 — why game edge is separate from Cloudflare web](../reference-design/13-game-networking-foundation/01-63-phase-54-why-game-edge-is-separate-from-cloudflare-web/index.md) |
| ⬜ `not-started` | [Phase 55 — relay bring-up](../reference-design/13-game-networking-foundation/02-64-phase-55-relay-bring-up/index.md) |

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
| ⬜ `not-started` | [Phase 56 — RKE2 etcd snapshots](../reference-design/14-backups-and-disaster-recovery/00-65-phase-56-rke2-etcd-snapshots/index.md) |
| ⬜ `not-started` | [Phase 57 — what must be backed up](../reference-design/14-backups-and-disaster-recovery/01-66-phase-57-what-must-be-backed-up/index.md) |
| ⬜ `not-started` | [Phase 58 — local vs offsite](../reference-design/14-backups-and-disaster-recovery/02-67-phase-58-local-vs-offsite/index.md) |
| ⬜ `not-started` | [Phase 59 — restore tests](../reference-design/14-backups-and-disaster-recovery/03-68-phase-59-restore-tests/index.md) |

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
| ⬜ `not-started` | [Phase 60 — Ansible control environment](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/00-69-phase-60-ansible-control-environment/index.md) |
| ⬜ `not-started` | [Phase 61 — inventory](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/01-70-phase-61-inventory/index.md) |
| ⬜ `not-started` | [Phase 62 — role ownership](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/02-71-phase-62-role-ownership/index.md) |
| ⬜ `not-started` | [Phase 63 — Ansible must be idempotent](../reference-design/15-consolidate-and-enforce-the-ansible-source-of-truth/03-72-phase-63-ansible-must-be-idempotent/index.md) |

### 0% — Part XVI — Ubuntu Autoinstall

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (3)</strong>
• Phase 64 — use Autoinstall for future clean rebuilds
• Phase 65 — minimal safe autoinstall skeleton
• Phase 66 — validate Autoinstall in a VM first</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 64 — use Autoinstall for future clean rebuilds](../reference-design/16-ubuntu-autoinstall/00-73-phase-64-use-autoinstall-for-future-clean-rebuilds/index.md) |
| ⬜ `not-started` | [Phase 65 — minimal safe autoinstall skeleton](../reference-design/16-ubuntu-autoinstall/01-74-phase-65-minimal-safe-autoinstall-skeleton/index.md) |
| ⬜ `not-started` | [Phase 66 — validate Autoinstall in a VM first](../reference-design/16-ubuntu-autoinstall/02-75-phase-66-validate-autoinstall-in-a-vm-first/index.md) |

### 0% — Part XVII — OpenTofu for external infrastructure

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (2)</strong>
• Phase 67 — what OpenTofu should own
• Phase 68 — state is sensitive</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase 67 — what OpenTofu should own](../reference-design/17-opentofu-for-external-infrastructure/00-76-phase-67-what-opentofu-should-own/index.md) |
| ⬜ `not-started` | [Phase 68 — state is sensitive](../reference-design/17-opentofu-for-external-infrastructure/01-77-phase-68-state-is-sensitive/index.md) |

### 0% — Part XVIII — Day-2 operations

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (7)</strong>
• Upgrade order
• RKE2 upgrade checklist
• Host kernel/NVIDIA update checklist
• Disk-pressure runbook
• Memory-pressure runbook
• CPU-pressure runbook
• Network-debugging layers</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Upgrade order](../reference-design/18-day-2-operations/00-78-upgrade-order/index.md) |
| ⬜ `not-started` | [RKE2 upgrade checklist](../reference-design/18-day-2-operations/01-79-rke2-upgrade-checklist/index.md) |
| ⬜ `not-started` | [Host kernel/NVIDIA update checklist](../reference-design/18-day-2-operations/02-80-host-kernel-nvidia-update-checklist/index.md) |
| ⬜ `not-started` | [Disk-pressure runbook](../reference-design/18-day-2-operations/03-81-disk-pressure-runbook/index.md) |
| ⬜ `not-started` | [Memory-pressure runbook](../reference-design/18-day-2-operations/04-82-memory-pressure-runbook/index.md) |
| ⬜ `not-started` | [CPU-pressure runbook](../reference-design/18-day-2-operations/05-83-cpu-pressure-runbook/index.md) |
| ⬜ `not-started` | [Network-debugging layers](../reference-design/18-day-2-operations/06-84-network-debugging-layers/index.md) |

### 0% — Part XIX — Failure modes you should explicitly design for

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (9)</strong>
• Root filesystem fills
• Developer gets compromised
• Developer has kubectl and tries privilege escalation
• CI runner is compromised
• Cilium breaks after upgrade
• Argo CD deletes something unexpectedly
• Admission policy locks out platform workloads
• GPU integration breaks containerd/RKE2
• Single server dies</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Root filesystem fills](../reference-design/19-failure-modes-you-should-explicitly-design-for/00-85-root-filesystem-fills/index.md) |
| ⬜ `not-started` | [Developer gets compromised](../reference-design/19-failure-modes-you-should-explicitly-design-for/01-86-developer-gets-compromised/index.md) |
| ⬜ `not-started` | [Developer has kubectl and tries privilege escalation](../reference-design/19-failure-modes-you-should-explicitly-design-for/02-87-developer-has-kubectl-and-tries-privilege-escalation/index.md) |
| ⬜ `not-started` | [CI runner is compromised](../reference-design/19-failure-modes-you-should-explicitly-design-for/03-88-ci-runner-is-compromised/index.md) |
| ⬜ `not-started` | [Cilium breaks after upgrade](../reference-design/19-failure-modes-you-should-explicitly-design-for/04-89-cilium-breaks-after-upgrade/index.md) |
| ⬜ `not-started` | [Argo CD deletes something unexpectedly](../reference-design/19-failure-modes-you-should-explicitly-design-for/05-90-argo-cd-deletes-something-unexpectedly/index.md) |
| ⬜ `not-started` | [Admission policy locks out platform workloads](../reference-design/19-failure-modes-you-should-explicitly-design-for/06-91-admission-policy-locks-out-platform-workloads/index.md) |
| ⬜ `not-started` | [GPU integration breaks containerd/RKE2](../reference-design/19-failure-modes-you-should-explicitly-design-for/07-92-gpu-integration-breaks-containerd-rke2/index.md) |
| ⬜ `not-started` | [Single server dies](../reference-design/19-failure-modes-you-should-explicitly-design-for/08-93-single-server-dies/index.md) |

### 0% — Part XX — Observability: how you know the platform works

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (5)</strong>
• Host SLO-style checks
• Kubernetes checks
• Tenant checks
• Build checks
• External-edge checks</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Host SLO-style checks](../reference-design/20-observability-how-you-know-the-platform-works/00-94-host-slo-style-checks/index.md) |
| ⬜ `not-started` | [Kubernetes checks](../reference-design/20-observability-how-you-know-the-platform-works/01-95-kubernetes-checks/index.md) |
| ⬜ `not-started` | [Tenant checks](../reference-design/20-observability-how-you-know-the-platform-works/02-96-tenant-checks/index.md) |
| ⬜ `not-started` | [Build checks](../reference-design/20-observability-how-you-know-the-platform-works/03-97-build-checks/index.md) |
| ⬜ `not-started` | [External-edge checks](../reference-design/20-observability-how-you-know-the-platform-works/04-98-external-edge-checks/index.md) |

### 0% — Part XXI — Recommended implementation sequence

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (9)</strong>
• Phase A — host foundation
• Phase B — Kubernetes foundation
• Phase C — GitOps + tenancy
• Phase D — policy + storage
• Phase E — platform services
• Phase F — developer workflow
• Phase G — external exposure
• Phase H — GPU
• Phase I — reproducibility</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Phase A — host foundation](../reference-design/21-recommended-implementation-sequence/00-99-phase-a-host-foundation/index.md) |
| ⬜ `not-started` | [Phase B — Kubernetes foundation](../reference-design/21-recommended-implementation-sequence/01-100-phase-b-kubernetes-foundation/index.md) |
| ⬜ `not-started` | [Phase C — GitOps + tenancy](../reference-design/21-recommended-implementation-sequence/02-101-phase-c-gitops-tenancy/index.md) |
| ⬜ `not-started` | [Phase D — policy + storage](../reference-design/21-recommended-implementation-sequence/03-102-phase-d-policy-storage/index.md) |
| ⬜ `not-started` | [Phase E — platform services](../reference-design/21-recommended-implementation-sequence/04-103-phase-e-platform-services/index.md) |
| ⬜ `not-started` | [Phase F — developer workflow](../reference-design/21-recommended-implementation-sequence/05-104-phase-f-developer-workflow/index.md) |
| ⬜ `not-started` | [Phase G — external exposure](../reference-design/21-recommended-implementation-sequence/06-105-phase-g-external-exposure/index.md) |
| ⬜ `not-started` | [Phase H — GPU](../reference-design/21-recommended-implementation-sequence/07-106-phase-h-gpu/index.md) |
| ⬜ `not-started` | [Phase I — reproducibility](../reference-design/21-recommended-implementation-sequence/08-107-phase-i-reproducibility/index.md) |

### 0% — Part XXII — Plain-English glossary

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (25)</strong>
• RKE2
• CNI
• Cilium
• Traefik
• Gateway API
• GitOps
• Argo CD
• ResourceQuota
• LimitRange
• Pod Security Admission
• Kyverno
• LocalPV
• OpenEBS LocalPV LVM
• Harbor
• BuildKit
• Buildx
• Skaffold
• LXD system container
• KVM VM
• Tailscale
• Cloudflare Tunnel
• WireGuard relay
• OpenTofu
• Idempotent
• Reconciliation</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [RKE2](../reference-design/22-plain-english-glossary/00-rke2/index.md) |
| ⬜ `not-started` | [CNI](../reference-design/22-plain-english-glossary/01-cni/index.md) |
| ⬜ `not-started` | [Cilium](../reference-design/22-plain-english-glossary/02-cilium/index.md) |
| ⬜ `not-started` | [Traefik](../reference-design/22-plain-english-glossary/03-traefik/index.md) |
| ⬜ `not-started` | [Gateway API](../reference-design/22-plain-english-glossary/04-gateway-api/index.md) |
| ⬜ `not-started` | [GitOps](../reference-design/22-plain-english-glossary/05-gitops/index.md) |
| ⬜ `not-started` | [Argo CD](../reference-design/22-plain-english-glossary/06-argo-cd/index.md) |
| ⬜ `not-started` | [ResourceQuota](../reference-design/22-plain-english-glossary/07-resourcequota/index.md) |
| ⬜ `not-started` | [LimitRange](../reference-design/22-plain-english-glossary/08-limitrange/index.md) |
| ⬜ `not-started` | [Pod Security Admission](../reference-design/22-plain-english-glossary/09-pod-security-admission/index.md) |
| ⬜ `not-started` | [Kyverno](../reference-design/22-plain-english-glossary/10-kyverno/index.md) |
| ⬜ `not-started` | [LocalPV](../reference-design/22-plain-english-glossary/11-localpv/index.md) |
| ⬜ `not-started` | [OpenEBS LocalPV LVM](../reference-design/22-plain-english-glossary/12-openebs-localpv-lvm/index.md) |
| ⬜ `not-started` | [Harbor](../reference-design/22-plain-english-glossary/13-harbor/index.md) |
| ⬜ `not-started` | [BuildKit](../reference-design/22-plain-english-glossary/14-buildkit/index.md) |
| ⬜ `not-started` | [Buildx](../reference-design/22-plain-english-glossary/15-buildx/index.md) |
| ⬜ `not-started` | [Skaffold](../reference-design/22-plain-english-glossary/16-skaffold/index.md) |
| ⬜ `not-started` | [LXD system container](../reference-design/22-plain-english-glossary/17-lxd-system-container/index.md) |
| ⬜ `not-started` | [KVM VM](../reference-design/22-plain-english-glossary/18-kvm-vm/index.md) |
| ⬜ `not-started` | [Tailscale](../reference-design/22-plain-english-glossary/19-tailscale/index.md) |
| ⬜ `not-started` | [Cloudflare Tunnel](../reference-design/22-plain-english-glossary/20-cloudflare-tunnel/index.md) |
| ⬜ `not-started` | [WireGuard relay](../reference-design/22-plain-english-glossary/21-wireguard-relay/index.md) |
| ⬜ `not-started` | [OpenTofu](../reference-design/22-plain-english-glossary/22-opentofu/index.md) |
| ⬜ `not-started` | [Idempotent](../reference-design/22-plain-english-glossary/23-idempotent/index.md) |
| ⬜ `not-started` | [Reconciliation](../reference-design/22-plain-english-glossary/24-reconciliation/index.md) |

### 0% — Part XXIII — Compact technical reference

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (9)</strong>
• Host ownership matrix
• Namespace reference
• Initial quota reference
• Host developer-limit reference
• Network exposure reference
• Storage reference
• Secret rules
• "Bad idea" reference
• First real application acceptance test</div></div>

| Status | Phase |
|--------|-------|
| ⬜ `not-started` | [Host ownership matrix](../reference-design/23-compact-technical-reference/00-108-host-ownership-matrix/index.md) |
| ⬜ `not-started` | [Namespace reference](../reference-design/23-compact-technical-reference/01-109-namespace-reference/index.md) |
| ⬜ `not-started` | [Initial quota reference](../reference-design/23-compact-technical-reference/02-110-initial-quota-reference/index.md) |
| ⬜ `not-started` | [Host developer-limit reference](../reference-design/23-compact-technical-reference/03-111-host-developer-limit-reference/index.md) |
| ⬜ `not-started` | [Network exposure reference](../reference-design/23-compact-technical-reference/04-112-network-exposure-reference/index.md) |
| ⬜ `not-started` | [Storage reference](../reference-design/23-compact-technical-reference/05-113-storage-reference/index.md) |
| ⬜ `not-started` | [Secret rules](../reference-design/23-compact-technical-reference/06-114-secret-rules/index.md) |
| ⬜ `not-started` | ["Bad idea" reference](../reference-design/23-compact-technical-reference/07-115-bad-idea-reference/index.md) |
| ⬜ `not-started` | [First real application acceptance test](../reference-design/23-compact-technical-reference/08-116-first-real-application-acceptance-test/index.md) |

### 0% — Part XXIV — Current verification references

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

| Status | Phase |
|--------|-------|

### 0% — Part XXV — Final build order

<div class="imp-tip" style="display:flex;align-items:center;gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;"><div style="display:flex;align-items:center;gap:8px;flex:1;"><div style="flex:1;height:8px;background:rgba(127,127,127,0.15);border-radius:999px;overflow:hidden;"><div class="imp-part-fill" style="--imp-w:0.0%;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);background-size:200% 100%;"></div></div><div style="font-size:.85em;font-weight:600;min-width:36px;text-align:right;">0%</div></div><div class="imp-tooltip"><strong>Done (0)</strong>
—
<hr style="opacity:.3;margin:6px 0;"><strong>Pending (0)</strong>
—</div></div>

| Status | Phase |
|--------|-------|

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