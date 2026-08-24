# configure RKE2's bundled Cilium

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

## default-deny tenants still need the kube-apiserver

On this self-hosted cluster the apiserver runs as a static pod on the node, so
the `kubernetes` Service backend is the **node IP**. Cilium CIDR selectors
(`ipBlock`) ignore node addressing by default, so a per-namespace egress
`default-deny` policy cannot be satisfied with an `ipBlock: 0.0.0.0/0` allow
rule — the apiserver backend is never matched.

Any tenant namespace under `default-deny` that needs the Kubernetes API (e.g. a
certificate self-signer job) must instead be covered by the cluster-wide
`kube-apiserver` entity policy. This is documented in
`05-gitops-bootstrap/default-deny-networkpolicy` and shipped as
`infra/kubernetes/platform/networkpolicies/00-allow-kube-apiserver.yaml`.

---