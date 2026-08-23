# choose and pin the RKE2 release

Use the RKE2 v1.36 line for this design.

Do not paste a floating release into production automation.

Record:

```yaml
rke2_minor: "v1.36"
rke2_version: "<EXACT_TESTED_RKE2_RELEASE>"
```

The install mechanism supports exact `INSTALL_RKE2_VERSION`.

Example shape:

```bash
curl -sfL https://get.rke2.io | \
  INSTALL_RKE2_VERSION='<EXACT_TESTED_RKE2_RELEASE>' sh -
```

Before installing, read:

```text
release notes for the selected patch
known issues
urgent Kubernetes upgrade notes
Cilium bundle version
Traefik bundle version
containerd version
```

---
