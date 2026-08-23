---
order: 54
---

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
address. The **proper solution is a Minecraft proxy** that carries the real
player IP at layer 7, where NAT does not matter.

#### Recommended architecture: a Minecraft proxy (Velocity) in front of the game

Put a **Velocity** (or BungeeCord) proxy in the relay path. The proxy connects
to the public-facing relay port; the real game server is a backend only the
proxy can reach. Velocity's **player-info forwarding** re-injects each player's
**real source IP** to the backend in the (signed) handshake — independent of
the NAT the relay does on the wire.

```text
Internet player
   |
   | TCP 25565/30079
   v
UAE VPS 89.36.162.171  --DNAT+MASQUERADE-->  alpha wg0
   |                                             |
   |    NodePort (proxy)                         v
   |   Velocity proxy pod  (it read the player's real IP from the wire)
   |     |  player-info-forwarding (signed handshake)
   |     v
   |   game backend pod  <-- sees the REAL player IP (from forwarding)
   v
  done
```

Key verified mechanics (from Velocity/PaperMC docs and itzg images):

- The **proxy** (`itzg/bungeecord:java17` with `TYPE=VELOCITY`) is what
  accepts the player-facing connection. It sees the client's real source IP on
  the wire when it talks to the relay, because the relay MASQUERADE hides it —
  **but the proxy can still relay that socket's peer address** into the
  forwarding handshake it sends to the backend. NAT between the player and the
  proxy does not matter for player-IP preservation.
- **Backend** (the actual game, `itzg/minecraft-server` with `TYPE=PAPER`)
  runs with `ONLINE_MODE=false` in `server.properties` — the proxy does all
  authentication/verification.
- **Forwarding config** must match exactly on both sides:
  - proxy `velocity.toml`: `player-info-forwarding-mode = "modern"` and a
    shared `forwarding-secret`.
  - backend `paper-global.yml`: `proxies.velocity.enabled=true`,
    `proxies.velocity.online-mode=true`, matching `secret`, and
    `proxies.velocity.forwarding-mode=modern`.
- The backend then logs and sees **each player's real public IP** (not the
  proxy's IP and not `10.200.0.1`), because modern forwarding carries it
  cryptographically.
- The proxy itself runs inside the cluster as a pod (e.g. `itzg/bungeecord`),
  exposed via the NodePort / relay instead of the game directly.

This is the correct architecture when game admins need player IPs (ban/geo/
log). For a throwaway demo, the relay keeps **MASQUERADE** and the pod sees
`10.200.0.1`, which is fine.

#### Alternative options (not recommended unless the proxy is too heavy)

- **Run the game on the relay's IP** (bind the game to `10.200.0.2` on alpha as
  a plain process, not in a pod) so Pro Custodibus policy routing applies.
- **Accept the relay's MASQUERADE** (pod sees `10.200.0.1`) and log the player
  address at a layer that already has it (e.g. a reverse proxy before NAT).

> **Fallback note (containers on a bridge on the same host):** Pro Custodibus's
> "Connection Marking" (CONNMARK on NEW via wg0; restore mark on return; route
> marked packets via a custom table) works when the container/bridge is **on
> the same host as the wg IP** so the reply is still sourced from the host's wg
> IP. It does **not** fix the Kubernetes pod case above.

---
