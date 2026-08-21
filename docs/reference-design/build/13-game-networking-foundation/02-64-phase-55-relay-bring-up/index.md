# Phase 55 — relay bring-up

Start with one relay candidate.

Recommended experimental order:

```text
1. OCI UAE Always Free if capacity/account conditions allow
2. low-cost Dubai VPS
3. paid OCI/AWS/Azure UAE if reliability requirements justify it
```

Do not permanently choose on provider marketing.

Benchmark:

```bash
ping
mtr
iperf3
iperf3 -u
```

Measure:

```text
median latency
p95
p99
jitter
packet loss
evening peak behavior
real UAE mobile path
GCC path if relevant
```

## Return-path design (player IP)

The relay currently **MASQUERADEs** inbound game flows, so the game pod sees the
relay's tunnel IP (`10.200.0.1`). This is the working, pragmatic default.

**Tested (does NOT work):** removing the VPS MASQUERADE and using Pro Custodibus
policy routing / connection marking on alpha to preserve the real player IP.
Both fail for a **Kubernetes pod behind Cilium**, because the pod replies with
its own pod IP (`10.42.x`), not alpha's tunnel IP (`10.200.0.2`), so the VPS
conntrack can't reverse-NAT the reply back to the client and the `SYN-ACK` is
dropped (external probe times out; reachability returns the moment MASQUERADE
is re-added).

See **Phase 54** for the full decision tree. Real options to expose the actual
player IP into a pod require a Minecraft proxy (BungeeCord/Velocity) or running
the game bound to the relay's IP as a plain process.

---
