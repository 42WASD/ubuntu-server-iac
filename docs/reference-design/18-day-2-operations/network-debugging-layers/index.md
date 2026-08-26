# Network-debugging layers

Debug in this order:

```text
1. host route/DNS
2. Tailscale
3. RKE2 node health
4. Cilium
5. Kubernetes Service
6. NetworkPolicy
7. Traefik/Gateway
8. Cloudflare
```

Do not start by disabling Cilium or the firewall.

Example commands:

```bash
ip route
resolvectl status
tailscale status

kubectl get nodes
kubectl -n kube-system get pods

kubectl get svc -A
kubectl get networkpolicy -A

kubectl -n kube-system logs <cilium-pod>
kubectl -n kube-system logs <traefik-pod>
```

## Cilium layer — the stale-node-IP check

If pods crash with network timeouts (DNS timeouts, `dial tcp ... connection
timed out`) **after any node IP change or reboot**, and the app/policy/configs
all look correct, check Cilium's persisted `CiliumEndpoint` (CEP) CRs against
the node's current IP **before** assuming a policy bug.

The host, RKE2 `node-ip`, and netplan may all be correct while the **CEP CRs
still store the old node IP**. Cilium then refuses to program those endpoints'
datapath ("endpoint sync cannot take ownership of CEP that is not local"),
silently breaking pod-to-pod + DNS traffic for every affected pod.

Go-to commands (full playbook in the runbook
`_runbook/13-game-networking-foundation/cilium-stale-node-ip-recovery`):

```bash
# does Cilium complain about a stale node IP?
kubectl -n kube-system logs ds/cilium --tail=200 | grep -iE "cannot take ownership|not local"

# count CEPs by recorded node IP
kubectl get cep -A -o json | python3 -c '
import sys, json
from collections import Counter
d = json.load(sys.stdin)
print(Counter(i["status"]["networking"]["node"] for i in d["items"]))'

# the node's actual current IP
kubectl get node alpha -o wide
```

If any CEP records an IP that is not the node's current IP, **delete the stale
CEPs AND restart the Cilium agent** so it regenerates them with the correct
node IP. Restarting the agent is mandatory — deleting CEPs alone only
regenerates a few.

---
