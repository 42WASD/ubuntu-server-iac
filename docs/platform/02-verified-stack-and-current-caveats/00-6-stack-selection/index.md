# Stack selection

| Layer | Selected tool | Why |
|---|---|---|
| Host OS | Ubuntu 26.04 LTS Server | normal Linux administration, AppArmor, systemd, current LTS |
| Host automation | Ansible | idempotent Linux configuration over SSH |
| Bare-metal reinstall | Ubuntu Autoinstall | repeatable OS install |
| Kubernetes | RKE2 | production-oriented Kubernetes distribution, embedded etcd, bundled components |
| Container runtime | RKE2 embedded containerd | no host Docker daemon required |
| CNI | Cilium | eBPF networking, NetworkPolicy, observability path |
| Ingress | Traefik | native RKE2 choice for new v1.36 clusters |
| Deployment / CD | Argo CD | GitOps + strong UI + multi-team model |
| Policy | Pod Security Admission + Kyverno | baseline/restricted policy + custom organization rules |
| Local K8s storage | OpenEBS LocalPV LVM | dynamic local LVM-backed PVCs without fake single-node replication |
| Registry | Harbor | private image registry, projects, retention, scanning |
| Metrics | Prometheus + kube-state-metrics + node-exporter | platform metrics |
| UI | Grafana | metrics/log visualization |
| Logs | Loki + Grafana Alloy | centralized logs |
| Build backend | BuildKit | remote, cached image builds |
| Dev loop | Skaffold | watch/build/test/deploy/log loop |
| Build isolation | LXD containers + KVM VMs where needed | low overhead for trusted builders, stronger boundary for untrusted builds |
| Private management | Tailscale | SSH/K8s/admin reachability without public SSH |
| Public web | Cloudflare | DNS/CDN/WAF/Tunnel/Access |
| Public game edge | UAE VPS + WireGuard | generic TCP/UDP relay |
| External IaC | OpenTofu | provider-managed resources from Git |

---
