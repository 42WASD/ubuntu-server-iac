# Host ownership matrix

| Resource | Owner |
|---|---|
| `/etc/ssh/**` | Ansible |
| `/etc/nftables.conf` | Ansible |
| `/etc/systemd/**` developer limits | Ansible |
| `/etc/rancher/rke2/config.yaml` | Ansible |
| RKE2 binary/version | Ansible |
| Cilium bootstrap HelmChartConfig | Ansible/bootstrap Git |
| Kubernetes namespaces | Argo CD |
| Kyverno policies | Argo CD |
| OpenEBS | Argo CD |
| StorageClasses | Argo CD |
| Monitoring | Argo CD |
| Harbor | Argo CD |
| Tenant applications | tenant GitOps |
| BuildKit | Ansible on build01 |
| Build cache | BuildKit GC |
| Cloudflare/relay cloud resources | OpenTofu |
| secrets | secret manager/Vault-encrypted workflow, not plaintext Git |

---
