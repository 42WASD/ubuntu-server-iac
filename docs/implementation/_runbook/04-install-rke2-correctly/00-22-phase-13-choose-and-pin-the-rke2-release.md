---
phase: 04-install-rke2-correctly/choose-and-pin-the-rke2-release
---

# Phase 13 — choose and pin the RKE2 release

**Intent:** pick one exact, tested RKE2 release and record it in Git so nothing
ever floats on `latest`. The install automation (Phase 16) must install exactly
this version, reproducibly.

## 13.1 State before this phase

RKE2 is **not yet installed** on `alpha`. Only the data-directory mount from
Phase 10 exists (Phase 10 carved a dedicated 320G XFS on NVMe for RKE2):

```bash
$ which rke2 rke2-server        # (no output -> not installed)
$ rke2 --version                # bash: rke2: command not found
$ systemctl list-units | grep -i rke2
# var-lib-rancher-rke2.mount  loaded active mounted /var/lib/rancher/rke2
$ ls -la /var/lib/rancher/rke2
# drwxr-xr-x 2 root root 6 ... .
```

So this phase only chooses and pins the version. Installation happens in
Phase 16.

## 13.2 Choose the exact release (v1.36 line)

The reference design pins the RKE2 **v1.36** line. To get the latest stable
patch we queried the RKE2 GitHub releases for non-prerelease `v1.36*` tags:

```bash
curl -sfL "https://api.github.com/repos/rancher/rke2/releases?per_page=40" \
  | python3 -c "import sys,json; rs=json.load(sys.stdin); \
  [print(r['tag_name'], r['prerelease']) for r in rs \
   if 'v1.36' in r['tag_name'] and 'rc' not in r['tag_name']]"
# v1.36.3+rke2r1 False     <- latest stable, not prerelease
# v1.36.2+rke2r1 False
```

**Pinned release: `v1.36.3+rke2r1`** (published 2026-08-04, `prerelease: False`).

We record it in the infra source-of-truth (`rke2_server` role defaults) as an
exact string, not a float:

<table>
<thead><tr><th>Key</th><th>Value</th><th>Meaning</th></tr></thead>
<tbody>
<tr><td><code>rke2_minor</code></td><td><code>"v1.36"</code></td><td>minor line for this design</td></tr>
<tr><td><code>rke2_version</code></td><td><code>"v1.36.3+rke2r1"</code></td><td>exact tested patch</td></tr>
</tbody>
</table>

**Infra encoding:** `infra/ansible/roles/rke2_server/defaults/main.yml`.

The Phase 16 installer consumes this exact string:

```bash
curl -sfL https://get.rke2.io | \
  INSTALL_RKE2_VERSION='v1.36.3+rke2r1' sh -
```

## 13.3 Release-note review (read before installing)

Read the selected patch's release notes, known issues, and urgent Kubernetes
upgrade notes. Key findings for **v1.36.3+rke2r1**:

- **Kubernetes v1.36.3**.
- **Traefik is now the DEFAULT ingress for new clusters** — `ingress-nginx` was
  retired upstream (March 2026). New clusters get Traefik; existing clusters keep
  their current ingress on upgrade. The `rke2-images-traefik` standalone tarball
  is gone (Traefik images now live in `rke2-images-core`).
- **Traefik chart v40.x has a breaking change** for ingress-nginx migration: the
  provider name changes from `kubernetesIngressNginx` to `kubernetesIngressNGINX`
  (see traefik-helm-chart v40.0.0).
- **Token note:** if servers aren't started with `--token`, a randomized token
  is generated at first cluster startup and used to join nodes and encrypt
  bootstrap data. It lives at `/var/lib/rancher/rke2/server/token` — must be
  retained for restore. (We will pin `--token` explicitly in Phase 14.)

Bundled component versions in this release (for later verification):

<table>
<thead><tr><th>Component</th><th>Version</th></tr></thead>
<tbody>
<tr><td>Cilium</td><td>v1.19.6</td></tr>
<tr><td>rke2-cilium chart</td><td>1.19.601</td></tr>
<tr><td>Traefik</td><td>v3.7.8</td></tr>
<tr><td>rke2-traefik chart</td><td>40.1.009</td></tr>
<tr><td>containerd</td><td>v2.3.3-k3s1</td></tr>
<tr><td>etcd</td><td>v3.6.14-k3s1</td></tr>
<tr><td>CoreDNS</td><td>v1.14.6</td></tr>
</tbody>
</table>

## 13.4 Checkpoint

- [x] Exact release chosen: `v1.36.3+rke2r1`
- [x] Not a floating tag — pinned as a literal in Git (`rke2_server` role defaults)
- [x] Release notes reviewed; Traefik-defaults ingress change and token note recorded
- [x] Bundle versions (Cilium/Traefik/containerd/etcd/CoreDNS) recorded

---

**Infra encoding:**
- `infra/ansible/roles/rke2_server/defaults/main.yml` — `rke2_minor`, `rke2_version`,
  `rke2_bundle.*` (source of truth for the pin).
- `infra/ansible/roles/rke2_server/tasks/main.yml` — stub with the exact install
  shape for Phase 16 (`INSTALL_RKE2_VERSION='{{ rke2_version }}'`).
- Nothing was installed on the host in this phase.