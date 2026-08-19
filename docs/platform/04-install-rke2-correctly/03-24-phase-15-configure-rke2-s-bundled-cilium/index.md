# Phase 15 — configure RKE2's bundled Cilium

Do not install a second upstream Cilium Helm release on top of RKE2's packaged Cilium.

Configure the packaged chart.

Create:

```bash
sudo mkdir -p /var/lib/rancher/rke2/server/manifests
sudoedit /var/lib/rancher/rke2/server/manifests/rke2-cilium-config.yaml
```

Use:

```yaml
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: rke2-cilium
  namespace: kube-system
spec:
  valuesContent: |-
    kubeProxyReplacement: true

    k8sServiceHost: localhost
    k8sServicePort: "6443"

    hubble:
      enabled: true
      relay:
        enabled: true
      ui:
        enabled: false
```

Why disable Hubble UI initially?

Because:

```text
metrics/observability backend first
admin UI exposure later
```

Do not create another web admin surface before private access policy exists.

---
