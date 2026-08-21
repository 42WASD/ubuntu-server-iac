---
phase: 13-game-networking-foundation/01-63-phase-54-why-game-edge-is-separate-from-cloudflare-web
---
# Phase 54 — why game edge is separate from Cloudflare web

**Intent:** record the deliberate design decision that the public **game**
edge is a separate traffic plane from the public **web** edge. This keeps
Cloudflare's strengths on HTTP/HTTPS and avoids forcing raw game TCP/UDP
through a path that cannot carry it cleanly.

## 54.1 The two planes

Web:

```text
Cloudflare Tunnel / proxy
```

Generic game TCP/UDP:

```text
UAE VPS
  -> WireGuard
  -> alpha / game Service
```

## 54.2 Why not route games through Cloudflare

- Cloudflare Tunnel is an HTTP(S)-centric proxy; it is **not** the generic
  free raw-UDP solution. Arbitrary game protocols (high-volume TCP + UDP, low
  latency, client-controlled ports) do not map cleanly onto the web tunnel.
- Game traffic wants a low-latency public endpoint close to players. The UAE
  relay VPS + WireGuard gives a generic TCP/UDP path into the cluster when
  home networking cannot expose ports cleanly.

## 54.3 Implementation consequence

The two planes stay separate end to end:

```text
public web   -> Cloudflare  -> cloudflared -> Traefik   -> HTTP Service
public game  -> UAE VPS     -> WireGuard   -> game Service (UDP/TCP)
```

Phase 53's `default-deny` NetworkPolicy stays; when a real game workload
lands, a **controlled external ports** policy exposes exactly the required
game ports on the game lane (not on the web plane).