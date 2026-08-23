---
order: 2
---

# Version policy

Never build this platform around floating `latest`.

Use this model:

```text
Git records:
  Ubuntu release
  RKE2 minor
  exact tested RKE2 patch
  Argo CD version
  OpenEBS chart version
  Kyverno chart version
  Harbor chart version
  monitoring chart versions
```

Example variable file:

```yaml
platform_versions:
  rke2: "<PINNED_RKE2_VERSION>"
  argocd: "<PINNED_ARGOCD_VERSION>"
  openebs: "<PINNED_OPENEBS_CHART_VERSION>"
  kyverno: "<PINNED_KYVERNO_CHART_VERSION>"
  harbor: "<PINNED_HARBOR_CHART_VERSION>"
```

Rule:

```text
discover latest
    !=
automatically deploy latest
```

Instead:

```text
discover current release
-> read release notes
-> update version in Git
-> test
-> deploy
```

---
