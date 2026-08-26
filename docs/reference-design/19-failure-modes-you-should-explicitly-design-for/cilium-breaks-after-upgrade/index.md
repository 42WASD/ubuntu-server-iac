# Cilium breaks after upgrade

Mitigation:

```text
pin RKE2
read bundled Cilium release notes
snapshot etcd
change one platform layer at a time
keep console/Tailscale access to host
do not simultaneously alter nftables + Cilium + RKE2
```

## Stale CiliumEndpoints after a node IP change

A node IP change (e.g. DHCP → pinned static IP) is a first-class trigger for
this failure mode, not just upgrades. The persisted `CiliumEndpoint` (CEP) CRs
still carry the **old** node IP; Cilium refuses to program the datapath for
"not local" endpoints, so pods crash with DNS/connection timeouts.

Signature in Cilium logs:

```text
endpoint sync cannot take ownership of CEP that is not local:
CEP's pod "...", pod's hostIP "<OLD_IP>", cilium nodeIP "<NEW_IP>"
```

**Recovery (delete stale CEPs + restart the agent — both are required):**

```bash
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml

# count CEPs by node; any entry != current node IP is stale
kubectl get cep -A -o json | python3 -c '
import sys, json
from collections import Counter
d = json.load(sys.stdin)
print(Counter(i["status"]["networking"]["node"] for i in d["items"]))'

# delete each stale CEP (node == OLD_IP), then restart the agent
kubectl -n kube-system rollout restart daemonset cilium
kubectl -n kube-system rollout status ds/cilium --timeout=180s
```

Full playbook: `_runbook/13-game-networking-foundation/cilium-stale-node-ip-recovery`.

---
