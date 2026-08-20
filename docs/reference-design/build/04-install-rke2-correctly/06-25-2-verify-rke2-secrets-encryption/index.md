# verify RKE2 Secrets encryption

RKE2 includes Secrets-at-rest encryption and the `secrets-encrypt` administration command.

Check:

```bash
sudo rke2 secrets-encrypt status
```

Expected:

```text
Encryption Status: Enabled
```

Do **not** rotate keys during initial bootstrap. Key rotation is a separate maintenance procedure and should be preceded by an etcd snapshot.

---

## Checkpoint 10 — THE BASE CLUSTER GATE

Do not continue until all are true:

```text
alpha = Ready
CoreDNS = Running
Cilium = Running
Traefik = Running
metrics-server = Running or intentionally pending while bootstrapping
DNS works inside a Pod
service networking works
no unexplained repeated restarts
```

Take a snapshot of state:

```bash
sudo /var/lib/rancher/rke2/bin/kubectl \
  --kubeconfig /etc/rancher/rke2/rke2.yaml \
  get all -A > ~/platform-audit/k8s-first-healthy.txt
```

---
