---
order: 24
---

# Part XXIV — Current verification references

The following primary/current documentation was used to verify the implementation direction. Re-audit these before major upgrades because infrastructure contracts change.

1. **RKE2 Requirements**  
   https://docs.rke2.io/install/requirements  
   Confirms general Linux/systemd/iptables expectation, host/network requirements, inotify guidance, node ports, and Cilium-specific network requirements.

2. **RKE2 Quick Start**  
   https://docs.rke2.io/install/quickstart  
   Confirms installation service model, kubeconfig location, and RKE2 startup pattern.

3. **RKE2 Configuration**  
   https://docs.rke2.io/install/configuration  
   Confirms `/etc/rancher/rke2/config.yaml` and current kubelet configuration approaches.

4. **RKE2 Server Configuration Reference**  
   https://docs.rke2.io/reference/server_config  
   Confirms CNI selection, ingress-controller selection, `disable-kube-proxy`, TLS SAN, snapshot and runtime configuration fields.

5. **RKE2 Embedded Datastore**  
   https://docs.rke2.io/datastore/embedded  
   Confirms embedded etcd is RKE2's default embedded datastore and SQLite is experimental.

6. **RKE2 Backup and Restore**  
   https://docs.rke2.io/datastore/backup_restore  
   Confirms etcd snapshot management and S3-compatible off-host snapshot support.

7. **RKE2 Cilium networking options**  
   https://docs.rke2.io/networking/basic_network_options  
   Confirms bundled Cilium configuration and kube-proxy replacement integration.

8. **RKE2 Secrets Encryption**  
   https://docs.rke2.io/security/secrets_encryption  
   Confirms Secrets-at-rest encryption status/rotation tooling and the default AES-CBC provider.

9. **RKE2 GPU Operators**  
   https://docs.rke2.io/add-ons/gpu_operators  
   Confirms RKE2-specific NVIDIA GPU Operator/containerd integration details and warns that GPU Operator changes can restart RKE2.

10. **NVIDIA GPU Operator platform support**  
   https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/platform-support.html  
   Current matrix used for the Ubuntu 26.04 validation caveat.

11. **Ubuntu NVIDIA driver installation**  
    https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/  
    Confirms `ubuntu-drivers` as the recommended command-line driver installation approach and server/compute driver options.

12. **Ubuntu Autoinstall configuration reference**  
    https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html  
    Confirms YAML structure, storage layouts, LVM behavior, disk matching, SSH identity, and action-based storage configuration.

13. **Ubuntu Autoinstall provisioning guide**  
    https://canonical-subiquity.readthedocs-hosted.com/en/latest/tutorial/providing-autoinstall.html  
    Confirms cloud-init / media delivery modes.

14. **Argo CD Getting Started**  
    https://argo-cd.readthedocs.io/en/latest/getting_started/  
    Confirms official install flow and recommends pinning a concrete Argo CD version for production.

15. **Argo CD Installation**  
    https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/  
    Confirms multi-tenant deployment model.

16. **OpenEBS Installation**  
    https://openebs.io/docs/main/quickstart-guide/installation  
    Confirms current unified install direction and LocalPV configuration considerations.

17. **OpenEBS LocalPV LVM StorageClass**  
    https://openebs.io/docs/user-guides/local-storage-user-guide/local-pv-lvm/configuration/lvm-create-storageclass  
    Confirms LocalPV LVM provisioner, `vgpattern`/`volgroup`, filesystems, scheduling, and expansion options.

18. **OpenEBS LocalPV prerequisites**  
    https://openebs.io/docs/main/quickstart-guide/prerequisites  
    Confirms LVM utilities / kernel module / VG prerequisites.

19. **Kyverno Installation**  
    https://kyverno.io/docs/installation/installation/  
    Confirms Helm is the recommended production installation method and Kyverno belongs in a dedicated namespace.

20. **Kubernetes Pod Security Admission**  
    https://kubernetes.io/docs/concepts/security/pod-security-admission/  
    Confirms namespace-level `privileged`, `baseline`, and `restricted` Pod Security enforcement.

21. **Kubernetes ResourceQuota**  
    https://kubernetes.io/docs/concepts/policy/resource-quotas/  
    Confirms namespace aggregate resource enforcement.

22. **Kubernetes LimitRange**  
    https://kubernetes.io/docs/concepts/policy/limit-range/  
    Confirms default/min/max resource constraints at namespace admission.

23. **Docker Buildx remote driver**  
    https://docs.docker.com/build/builders/drivers/remote/  
    Confirms Buildx can connect to externally managed BuildKit and supports TLS client configuration.

24. **BuildKit cache garbage collection**  
    https://docs.docker.com/build/cache/garbage-collection/  
    Confirms automatic cache GC and age/size policy model.

25. **Skaffold dev loop**  
    https://skaffold.dev/docs/workflows/dev/  
    Confirms source watching, file sync/build/test/deploy/log development workflow.

26. **Tailscale Linux install**  
    https://tailscale.com/kb/1031/install-linux  
    Confirms Linux installation and `tailscale up` path.

27. **Cloudflare Tunnel**  
    https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/  
    Confirms outbound tunnel architecture for published/private applications.

28. **OpenTofu providers/state**  
    https://opentofu.org/docs/language/providers/  
    https://opentofu.org/docs/language/state/  
    Confirms provider dependency/configuration model and state handling.

