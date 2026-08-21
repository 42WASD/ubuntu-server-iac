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
source to the relay's WireGuard IP). The validated approach is **policy
routing on the private side** (reference: Pro Custodibus "WireGuard Port
Forwarding From the Internet", "Policy Routing" section):

```text
VPS (public)                alpha (home)
  DNAT public:port           wg0 return-route table
  -> wg0 (NO MASQUERADE)      ip rule -> custom table
        |                          |
        v                          v
   Internet player          game pod sees real player IP
```

Rules on the private host (alpha):

```text
[Interface] ... Table = <N>
PreUp   = ip rule add from 10.200.0.2 table <N> priority 456
PostDown= ip rule del from 10.200.0.2 table <N> priority 456
```

- Remove MASQUERADE from the VPS so the player source IP survives the tunnel.
- On alpha, route **only** return traffic (source = its WireGuard IP) back
  through the tunnel via a custom table; all other alpha traffic keeps its
  normal ISP gateway.

**Kubernetes caveat:** a Kubernetes Service (`kube-proxy`/CNI) can re-SNAT
packets before they reach a pod. Use `externalTrafficPolicy: Cluster` for
connection-preserving behavior, and verify the pod sees the real source IP
end-to-end:

```text
VPS sees 203.0.113.50      -> player's real IP
alpha sees 203.0.113.50
pod sees 203.0.113.50      <-- the important one
```

If the pod sees a `10.x`/node IP instead, the rewrite is happening inside
Kubernetes (CNI/service), not WireGuard.

> **Fallback — Connection Marking:** if the private server is behind another
> layer (e.g. a container/pod bridge) so simple policy routing can't determine
> the return path, use connection marking: mark NEW connections that arrive via
> wg0 with `CONNMARK`, restore the mark on return packets, and route marked
> packets via a custom table. See Pro Custodibus "WireGuard Port Forwarding to
> Other Networks" (Connection Marking) section.

---
