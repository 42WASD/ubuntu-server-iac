# Phase 54 — why game edge is separate from Cloudflare web

Web:

```text
Cloudflare Tunnel / proxy
```

Generic game TCP/UDP:

```text
UAE VPS
-> WireGuard
-> alpha/game Service
```

Cloudflare Tunnel is not the generic free raw-UDP solution.

Keep the two traffic planes separate.

## Source-IP design (preserve real player IP)

For game services the game server should see the **real player IP**, not the
relay's tunnel address. This rules out plain MASQUERADE (which rewrites the
source to the relay's WireGuard IP). The correct technique depends entirely
on **where the service replies from** — see the decision tree below.

### Does it work for a Kubernetes pod? (tested — no)

We implemented and tested the two documented Pro Custodibus return-path
techniques (Policy Routing, then Connection Marking) for this relay. Both
**fail** for a workload that is a **Kubernetes pod behind Cilium**. The root
cause:

```text
VPS (public 89.36.162.171)      alpha (wg0 10.200.0.2)
  DNAT public:30079                 |->  NodePort 30079 -> pod 10.42.x.x
  ^/ wg0 (10.200.0.1)  NO MASQ      |
        |                            |
   client SYN (src player IP)        pod replies with src = POD IP (10.42.x)
```

- Pro Custodius "Policy Routing"/"Connection Marking" assume the **service
  itself binds the tunnel/wg IP** (a plain process on the private host), so
  return packets are sourced from the wg IP and the VPS conntrack
  reverse-NATs them back to the client.
- A Kubernetes pod replies with its **own pod IP** (e.g. `10.42.0.x`), not
  `10.200.0.2`. The VPS conntrack only knows the DNAT target `10.200.0.2`, so a
  reply sourced from a pod IP does not match a tracked connection; it is treated
  as a brand-new flow and dropped (`SYN` reaches the pod but the `SYN-ACK`
  never returns to the client).

**Verified observation:** with the VPS MASQUERADE removed and policy/connection
marking in place on alpha, an external TCP probe to `89.36.162.171:30079`
timed out; re-adding the VPS MASQUERADE immediately restored reachability.

### Decision tree (Pro Custodibus, "Port Forwarding From the Internet")

1. Does the private service need the original client source IP?
   - **No** → use **MASQUERADE** on the VPS (this is what the relay does now;
     the pod sees `10.200.0.1`, which is fine when the app doesn't care).
   - **Yes** → continue.
2. Does the service reply from the relay's tunnel IP (`10.200.0.2`) directly
   (a plain process bound to the wg IP, not a container)?
   - **Yes** → use **policy routing** on alpha (`ip rule from 10.200.0.2 table
     <N>`; route return via wg0) — this is what Pro Custodibus documents.
   - **No** (it's a pod / container on a bridge) → **policy routing and
     connection marking alone cannot preserve the source IP** unless you also
     make the reply source the tunnel IP (see below).

### If you must preserve the player IP into a pod

Preserving the real player IP **end-to-end into a Kubernetes pod behind a
relay is not achievable with pure L3/L4 NAT** through this topology, because
conntrack NAT is symmetric and the pod does not source replies from the tunnel
address. Real options:

- **Minecraft proxy in front of the game** (BungeeCord/Velocity) that
  re-injects the player IP via a proxy/handshake (e.g. `proxy-protocol`, or the
  proxy runs in the cluster on the node and the game reads the real address).
- **Run the game on the relay's IP** (bind the game to `10.200.0.2` on alpha as
  a plain process, not in a pod) so Pro Custodibus policy routing applies.
- **Accept the relay's MASQUERADE** (pod sees `10.200.0.1`) and, if logging the
  player address matters, do it at a layer that already has it (e.g. a reverse
  proxy that logs the original client IP before NAT).

For the current demo, the relay keeps **MASQUERADE** and the pod sees
`10.200.0.1`. This is the pragmatic, working choice.

> **Fallback note (containers on a bridge on the same host):** Pro Custodibus's
> "Connection Marking" (CONNMARK on NEW via wg0; restore mark on return; route
> marked packets via a custom table) works when the container/bridge is **on
> the same host as the wg IP** so the reply is still sourced from the host's wg
> IP. It does **not** fix the Kubernetes pod case above.

---
