---
phase: 13-game-networking-foundation/02-64-phase-55-relay-bring-up
---
# Phase 55 — relay bring-up

**Intent:** start with **one relay candidate**, benchmark it honestly, and pick
it (or not) on measured data — never on provider marketing. The relay
candidate is the **confirmed-UAE Melbicom VPS** (the "low-cost UAE VPS" tier).

Reference order (tiers in order):

```text
1. OCI UAE Always Free        (if capacity/account conditions allow)
2. low-cost Dubai VPS         <- current candidate (Melbicom, confirmed UAE)
3. paid OCI/AWS/Azure UAE     (only if reliability requirements justify it)
```

## 55.1 Candidate

- Host: `89.36.162.171` (hostname `263347.melbi.space`, KVM-2-FJR)
- Confirmed **physically in UAE**: Cloudflare colo `DXB`, city Fujairah,
  AS `8849` (Melbikomas). Not a "paperwork AE" — a genuinely UAE-located box.

## 55.2 Benchmark suite (measured)

Tool `iperf3`/`traceroute`/`mtr` installed on the VPS. All runs from alpha.

**Latency (`ping`, 8 pkt):**

```text
min/avg/max/mdev = 21.8 / 28.6 / 33.9 / 3.9 ms, 0% loss
```

### `mtr` path (alpha -> VPS, 30 pkt):

```text
1  homerouter.cpe        0.4ms
3  10.100.136.54        18ms   (UAE backbone)
4  10.100.37.90         17ms
12 89.36.162.171       28.5ms  (3.3% loss, ICMP-only final hop)
```

### `iperf3` TCP (alpha -> VPS):

```text
single stream : 25.7 Mbits/sec sender, 16 retransmits
reverse (-R)  : 13.9 Mbits/sec (VPS -> alpha return path)
4 streams (-P4): 84.4 Mbit/s send / 81.6 recv
```

### `iperf3 -u` UDP (alpha -> VPS):

```text
10M       9.97 Mbit/s   jitter 1.477ms  loss  0.011%
20M (1200B game-size) 19.9 Mbit/s  jitter 0.514ms loss 0.012%
50M      49.4 Mbit/s   jitter 0.213ms loss  0.78%
100M     99.2 Mbit/s   jitter 0.172ms loss  0.34%
```

## 55.3 Interpretation

- Latency ~28 ms and 0% loss confirm a genuine, low-latency UAE path.
- UDP is the important one for games: even at 100 Mbit/s only 0.34% loss with
  ~0.17 ms jitter. At realistic game rates (10–20 Mbit/s) loss is ~0.01% —
  excellent.
- TCP single-stream ~25 Mbit/s is a per-flow/window limit, not the link: 4
  parallel streams reach ~84 Mbit/s, so the ceiling is well above single-game
  needs.
- The relay candidate passes the benchmark; the exact game-edge architecture
  and port mapping are intentionally **deferred** to a later decision
  (per Phase 53/54, the game edge plane is separate and chosen independently).

## 55.4 WireGuard relay tunnel (established)

The generic encrypted pipe between the VPS and alpha is **up and verified**.
This is transport infrastructure only — it carries no game-specific decision
(which ports, gateway shape, etc. are still deferred to the later
architecture choice, per Phase 53/54).

Topology: alpha is behind NAT, so **alpha connects out** to the VPS.

```text
alpha (wg0 10.200.0.2)  --outbound-->  VPS (public 89.36.162.171:51820, wg0 10.200.0.1)
```

Config (keys kept out of Git; the private keys live only on each host):

```text
/etc/wireguard/wg0.conf   on alpha   : Address 10.200.0.2/24, PersistentKeepalive 25
/etc/wireguard/wg0.conf   on VPS     : Address 10.200.0.1/24, ListenPort 51820
```

Both ends are boot-persistent:

```bash
systemctl enable wg-quick@wg0        # both alpha and VPS
```

VPS has forwarding enabled for the relay:

```bash
echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-wg-relay.conf && sysctl -p ...
```

Verify (both directions across tunnel `10.200.0.0/24`):

```bash
ping -c 5 10.200.0.1   # alpha -> VPS   : 0% loss, ~28ms
ping -c 5 10.200.0.2   # VPS   -> alpha : 0% loss, ~30ms
```

Tunnel throughput (iperf3 over the tunnel, VPS bound to 10.200.0.1):

```text
TCP through tunnel : 38.6 Mbit/s receiver (alpha -> VPS, 8s)
UDP through tunnel : 9.95 Mbit/s, jitter 1.9ms, loss 0.041% (10M game-like)
```

The WireGuard overhead is negligible — tunnel throughput actually matched the
public-IP path. No game ports are DNAT'd through it yet; that happens with the
game-edge architecture decision.

## 55.5 Tooling / notes

- `wireguard` + `wireguard-tools` installed on both the VPS and alpha (kernel
  module `wireguard` loaded).
- **Secrets:** the VPS root password is stored **outside the repo** at
  `~/.config/iac-secrets/` (0600, never committed). WireGuard private keys
  also live only on each host, never in Git. Alpha's SSH pubkey is authorized
  on the VPS for non-interactive admin.
- Evening-peak / real-UAE-mobile / GCC-path measurements are **ongoing** and
  will be appended here as they're taken.