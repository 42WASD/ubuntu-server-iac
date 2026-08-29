---
phase: 13-game-networking-foundation/game-server-orchestration-operator/cilium-stale-node-ip-recovery
---

# Runbook — Cilium stale-node-IP recovery (post-reboot pod crashes)

**Symptom:** after a node reboot, workloads in a default-deny tenant namespace
crash with DNS timeouts and `dial tcp ... connection timed out`. Looks like a
policy or app bug — it is not. Root cause is stale **CiliumEndpoint (CEP)**
CRs carrying the old DHCP node IP after the node was pinned to a static IP.

This page is the **go-to reference** for this class of failure. If you see pods
crashing with network timeouts after any node IP change, go straight here.

## The failure signature

In the crashing pod logs:

- Java (Velocity/Paper itzg images): `DnsNameResolverTimeoutException:
  fill.papermc.io ... /10.43.0.10:53 ... timed out`
- Nakama: `dial tcp cockroachdb-public:26257: connect: connection timed out`

A probe in the **affected namespace** gets `connection timed out; no servers
could be reached` for `nslookup ... 10.43.0.10`, while the same probe in the
`default` namespace resolves fine. That contrast points at the **CNI dataplane**
(Cilium), not at DNS/CoreDNS and not at the app.

## The Cilium log that proves it

```bash
kubectl -n kube-system logs ds/cilium --tail=200 | grep -iE "cannot take ownership|not local"
```

Output:

```text
error="endpoint sync cannot take ownership of CEP that is not local:
CEP's pod \"...\", pod's hostIP \"192.168.8.132\", cilium nodeIP \"192.168.8.240\")"
```

This repeats for **every** pod. Cilium refuses to program the datapath for
endpoints whose persisted CEP still records the **old** node IP.

## Root cause

The node's IP changed (DHCP `.132` → pinned static `.240`). The **persisted
`CiliumEndpoint` (CEP) CRs** still store `status.networking.node: 192.168.8.132`
while Cilium now runs at `192.168.8.240`. Cilium will not take ownership of
"not local" endpoints, so it never programs their datapath → all pod-to-pod and
pod-to-DNS traffic for those pods breaks.

Host, RKE2, and netplan may all be correct (`.240`) — the stale state is
**only** in Cilium's stored CEPs. Do not chase netplan/RKE2/netpols.

## Fix — steps 1 & 2 (mandatory)

**Deleting CEPs alone is NOT enough.** You must also restart the Cilium agent
so it re-discovers all local endpoints and rewrites every CEP with the correct
node IP.

```bash
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml

# 1. See the damage — count CEPs by node
kubectl get cep -A -o json | python3 -c '
import sys, json
from collections import Counter
d = json.load(sys.stdin)
print(Counter(i["status"]["networking"]["node"] for i in d["items"]))'

# 2. Delete every stale CEP (node == the OLD IP)
kubectl get cep -A -o json > /tmp/ceps.json
python3 - <<'PY'
import json, subprocess
d = json.load(open('/tmp/ceps.json'))
stale = [(i['metadata']['namespace'], i['metadata']['name'])
         for i in d['items']
         if i.get('status', {}).get('networking', {}).get('node') == '192.168.8.132']
print('stale count=', len(stale))
for ns, name in stale:
    subprocess.run(['kubectl', 'delete', 'cep', name, '-n', ns, '--ignore-not-found'])
PY

# 3. RESTART the Cilium agent so it regenerates ALL CEPs with the right node
kubectl -n kube-system rollout restart daemonset cilium
kubectl -n kube-system rollout status ds/cilium --timeout=180s
```

## Verify the fix

```bash
kubectl get cep -A | tail -n +2 | wc -l        # should equal the pod count (~43)
kubectl get cep -A -o json | python3 -c '
import sys, json
from collections import Counter
d = json.load(sys.stdin)
print(Counter(i["status"]["networking"]["node"] for i in d["items"]))'
# expect {'192.168.8.240': <N>} with 0 stale entries

kubectl -n kube-system logs ds/cilium --tail=50 | grep -ciE "cannot take ownership"
# expect 0
```

## Step 3 — recreate the crash-looping pods

Once the dataplane is healthy, `paper-lobby` (and similar) recover on their own.
For long-crash-looping deployments, delete the stale pods so the Deployment
recreates them fresh:

```bash
kubectl -n <tenant-ns> delete pod -l app=<app>
```

## Step 4 — the "one-way NetworkPolicy" trap (Nakama → CockroachDB)

A separate, common follow-on: after DNS works, an init container still cannot
reach a DB in the same namespace. The namespace is `default-deny` on **ingress
AND egress**. Kubernetes NetworkPolicies are **one-way**: an `allow-games-egress`
that lets Nakama **egress** to CockroachDB:26257 does **not** let the connection
in to the DB. The destination pod also needs a matching **ingress** allow from
the client.

Add a scoped ingress NetworkPolicy on the DB (same pattern as
`allow-proxy-to-paper-lobby`). See `clusters/alpha/networkpolicy.yaml` in the
`42wasd-mc` repo for the live `allow-nakama-to-cockroachdb` example.

## Verified end state (2026-08-26)

```text
cockroachdb-0    1/1  Running
nakama           1/1  Running  (×2)
paper-lobby      1/1  Running
velocity         1/1  Running  (×2)
```

Committed in `42wasd-mc` `82877a3`.

## Rule for the future

- **After any node IP change, restart the Cilium agent** (or delete stale CEPs
  AND restart). Never skip the restart.
- **`default-deny` on ingress+egress** ⇒ every intra-namespace flow needs a
  matching ingress allow on the destination, not just an egress allow on the
  source.
- **DNS timeouts in one namespace but not `default`** ⇒ suspect the CNI
  dataplane for those pods, not CoreDNS.