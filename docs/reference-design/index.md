# Ubuntu 26.04 LTS Production-Like Hosting Platform

**Audit / verification date:** 2026-08-19  
**Target:** one powerful Ubuntu 26.04 LTS Server host, designed to grow into multiple machines  
**Primary node name used in examples:** `alpha`  
**Build node name used in examples:** `build01`  
**Purpose:** explain the architecture in plain English **without removing the implementation detail**, then provide a gated runbook you can follow from a clean Ubuntu install to a usable RKE2 platform.

> **Important scope note:** This is a practical infrastructure runbook for a serious single-node platform. It is deliberately conservative around destructive disk operations, host firewalls, GPU runtime changes, and cluster-wide policy. Commands containing placeholders such as `<DISK>`, `<TAILSCALE_IP>`, `<PINNED_VERSION>`, or `<DOMAIN>` are **not paste-ready until you replace and verify them**.

> **Single-node reality:** Kubernetes gives you reconciliation, scheduling, policy, declarative state, and fast recovery after a normal reboot. One physical server is still **not high availability**. A motherboard, PSU, storage-controller, or host failure can take the whole platform down.

## How to use this runbook

Treat each phase as a transaction:

```text
READ
  -> CAPTURE CURRENT STATE
      -> CHANGE ONE LAYER
          -> VALIDATE
              -> COMMIT CONFIG TO GIT
                  -> CONTINUE
```

Notation used throughout:

```text
Checkpoint
    You must prove the listed conditions before continuing.

Template
    The structure is correct, but placeholders must be replaced.

Danger / destructive
    Device names, storage, credentials, or access can be lost if copied blindly.

Optional / later
    Not required to establish the base platform.
```

### Manual commands vs Ansible

The shell commands in this document are deliberately visible so you understand what the platform is doing.

The preferred operating pattern is **not** to finish the whole machine manually and automate months later.

Use:

```text
first time you learn a phase
    -> run/verify carefully
    -> immediately encode that phase in its Ansible role
    -> rerun the role
    -> verify idempotence
    -> move to the next phase
```

So the later Ansible section is a consolidation/reference section, not permission to leave the host undocumented until the end.

---

---

## Platform Map

- [I — Understand the platform before installing anything](01-understand-the-platform-before-installing-anything/index.md)
- [II — Verified stack and current caveats](02-verified-stack-and-current-caveats/index.md)
- [III — Build the host](03-build-the-host/index.md)
- [IV — Install RKE2 correctly](04-install-rke2-correctly/index.md)
- [V — GitOps bootstrap](05-gitops-bootstrap/index.md)
- [VI — Policy enforcement](06-policy-enforcement/index.md)
- [VII — Persistent storage](07-persistent-storage/index.md)
- [VIII — Monitoring and logs](08-monitoring-and-logs/index.md)
- [IX — Registry](09-registry/index.md)
- [X — Developer build experience](10-developer-build-experience/index.md)
- [XI — Public web path](11-public-web-path/index.md)
- [XII — GPU validation phase](12-gpu-validation-phase/index.md)
- [XIII — Game networking foundation](13-game-networking-foundation/index.md)
- [XIV — Backups and disaster recovery](14-backups-and-disaster-recovery/index.md)
- [XV — Consolidate and enforce the Ansible source of truth](15-consolidate-and-enforce-the-ansible-source-of-truth/index.md)
- [XVI — Ubuntu Autoinstall](16-ubuntu-autoinstall/index.md)
- [XVII — OpenTofu for external infrastructure](17-opentofu-for-external-infrastructure/index.md)
- [XVIII — Day-2 operations](18-day-2-operations/index.md)
- [XIX — Failure modes you should explicitly design for](19-failure-modes-you-should-explicitly-design-for/index.md)
- [XX — Observability: how you know the platform works](20-observability-how-you-know-the-platform-works/index.md)
- [XXI — Recommended implementation sequence](21-recommended-implementation-sequence/index.md)
- [XXII — Plain-English glossary](22-plain-english-glossary/index.md)
- [XXIII — Compact technical reference](23-compact-technical-reference/index.md)
- [XXIV — Current verification references](24-current-verification-references/index.md)
- [XXV — Final build order](25-final-build-order/index.md)
