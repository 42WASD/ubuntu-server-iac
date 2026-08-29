# Cilium stale node-IP recovery

Operational recovery procedure for a failure class hit on `alpha`: after a
node IP change, pods in default-deny namespaces crash with DNS/connection
timeouts although netplan, RKE2 and NetworkPolicies are all correct.

**Go to the full runbook on the implementation page** (Part XIII,
`game-server-orchestration-operator` → this subsection) for the complete
command sequence — this page records the pattern and the diagnosis path.

## Failure signature

- Pod logs: `DnsNameResolverTimeoutException ... 10.43.0.10:53 ... timed out`
  (Java/itzg images), `dial tcp ... connection timed out` (Nakama/others).
- `nslookup` from the affected namespace: `connection timed out; no servers
  could be reached`; the same probe in `default` resolves fine → the CNI
  dataplane is implicated, not DNS/CoreDNS and not the app.

## Root cause

A node IP change (DHCP → static pin) leaves **persisted `CiliumEndpoint`
CRs** recording the old node IP. Cilium refuses to "take ownership" of
endpoints whose CEP is "not local" (node IP mismatch) and never programs
their datapath:

```text
cannot take ownership of CEP that is not local:
CEP's pod "...", pod's hostIP "192.168.8.132", cilium nodeIP "192.168.8.240"
```

## Fix pattern (two mandatory steps)

1. Delete every stale CEP (CEPs whose `status.networking.node` equals the old
   node IP).
2. **Restart the Cilium agent** so it re-discovers local endpoints and
   rewrites CEPs with the correct node IP — deleting CEPs alone is NOT
   enough.

## Prevention

Pin the node IP **before** first cluster bring-up (this is exactly why the
design requires static `node-ip` in the RKE2 config, matched to netplan — see
Part III, inventory/host setup).
