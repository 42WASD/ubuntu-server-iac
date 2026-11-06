---
phase: 13-game-networking-foundation/public-hostname-and-relay-persistence
---
# Phase 57 — public hostname `mc-oompas.42base.com` + relay boot persistence

**Intent:** expose the ATM10SKY skyblock world to the public internet on a
friendly hostname, and make the relay's iptables rules survive a VPS reboot
without duplicate rules accumulating on every run.

Reference: Phase 55 (`relay-bring-up`) established *why* the game edge is a
separate relay. This phase records the hostname wiring and fixes a latent
boot-persistence bug in the relay script that would have taken **both** the
lobby and skyblock offline after any reboot.

## 57.1 Public name

| Record | Value | Proxy |
|---|---|---|
| `mc-oompas.42base.com` `A` | `89.36.162.171` | **DNS-only (grey cloud)** |

Grey cloud is **required**: Cloudflare's orange-cloud proxy only handles
HTTP(S) on 80/443/8443 etc. Minecraft speaks a raw TCP protocol on
25565/30080, which an HTTP proxy cannot carry. The A record must resolve
straight to the relay's origin IP.

Verified:

```bash
dig +short mc-oompas.42base.com A       # 89.36.162.171
dig +short 42base.com NS                # norm/katelyn.ns.cloudflare.com
dig +short SRV _minecraft._tcp.mc-oompas.42base.com   # (none)
```

## 57.2 Port map — the hostname is not enough on its own

`mc-oompas.42base.com` resolves to the relay, but **which game answers depends
entirely on the port**, because the relay multiplexes by port:

| Public address | Relay rule | Reaches |
|---|---|---|
| `mc-oompas.42base.com:30080` | range DNAT `30000:30199` | **ATM10SKY** skyblock |
| `mc-oompas.42base.com:25565` | alias DNAT `25565` -> `30079` | **Velocity** -> lobby |
| `89.36.162.171:30080` | same | ATM10SKY |
| `192.168.8.240:30080` | none (LAN) | ATM10SKY |

A Minecraft client asked for a bare hostname with no port dials **25565**,
which lands on the lobby proxy — *not* the skyblock world. Two ways to make the
skyblock world reachable by the plain hostname:

1. **Explicit port** — players enter `mc-oompas.42base.com:30080`. Works today,
   zero further changes. This is the current state.
2. **SRV record** — add `_minecraft._tcp.mc-oompas` SRV ->
   `0 5 30080 mc-oompas.42base.com`. The client then discovers port 30080 from
   the bare name. Minecraft clients honour SRV lookups natively.

Option 2 requires a **Cloudflare API token with `Zone:DNS:Edit` on
`42base.com`**. No such token exists on alpha, in `~/.config/iac-secrets/`, in
either repo, or in the cluster (the only Cloudflare credential present is the
`cloudflared-token` Secret in the `ingress` namespace, which is a *tunnel*
token and cannot edit DNS; `infra/tofu/cloudflare/` only captures that same
tunnel token into R2 state). The SRV record therefore has to be added either
by hand in the Cloudflare dashboard or after supplying a scoped token.

Verify which server answers a given endpoint with a protocol-level probe (a
bare TCP connect cannot tell two Minecraft servers apart):

```bash
python3 /tmp/mcping.py
```

```text
=== mc-oompas.42base.com:30080  [expected: ATM10SKY (skyblock)]
    version : 1.21.1
    motd    : 'All the Mods 10: To the Sky'
    players : 0/20
=== mc-oompas.42base.com:25565  [expected: velocity -> lobby]
    version : Velocity 1.7.2-26.3
    motd    : '&bWelcome to the 42WASD Minecraft network'
    players : 0/500
=== 89.36.162.171:30080  [expected: ATM10SKY (skyblock)]
    version : 1.21.1
    motd    : 'All the Mods 10: To the Sky'
=== 192.168.8.240:30080  [expected: ATM10SKY direct (no relay)]
    version : 1.21.1
    motd    : 'All the Mods 10: To the Sky'
```

## 57.3 Bug found: the relay script had no MASQUERADE rule

Phase 55.5 proved by experiment that MASQUERADE is **mandatory** on this relay
(with it off, an external probe to `:30079` times out; with it on, the port is
open). The live ruleset did have the rule. The **boot script did not** — its
only mention of MASQUERADE was in a comment, left over from the reverted
"Option 2 / preserve the real player IP" attempt, plus a trailing `# NOTE:
MASQUERADE intentionally removed for Option 2`.

Consequence: everything worked *now*, but the first `systemctl restart` or VPS
reboot would have installed DNAT only, and **both** the lobby and the skyblock
world would have gone dark externally with no obvious cause. A latent
time-bomb, not a cosmetic wart.

## 57.4 Bug found: grep-over-`iptables-save` idempotency guards never matched

The script guarded each rule with:

```bash
if ! $SAVE -t nat | grep -q -- "--dport 25565 -j DNAT --to-destination $GAME_DEST:$MC_NODEPORT$"; then ...
```

`iptables-save` does not echo your input back verbatim. It **normalises** and
**expands**:

| You write | `iptables-save` prints |
|---|---|
| `-d 10.200.0.2` | `-d 10.200.0.2/32` |
| `-p tcp` | `-p tcp -m tcp` |
| `--dport 25565` | `--dport 25565` (fine) |

So the MASQUERADE guard (expecting `-d 10.200.0.2 -j MASQUERADE`) and the MSS
clamp guard (expecting `-o wg0 -p tcp --tcp-flags ...`) **could never match**.
Every single run appended another copy. Five duplicate `TCPMSS` rules had
already accumulated:

```text
-A POSTROUTING -o wg0 -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1380
   ^^^ repeated 5x
```

Harmless in effect (an identical clamp is idempotent to the packet) but it
proved the guard was decorative, and the same class of bug would silently
duplicate the DNAT rules once their addresses changed.

**Fix:** every guard became a real `iptables -C` (check) — the kernel matches
the exact rule, no string formatting involved:

```bash
if ! $IP -t nat -C POSTROUTING -d "$GAME_DEST" -j MASQUERADE 2>/dev/null; then
  $IP -t nat -A POSTROUTING -d "$GAME_DEST" -j MASQUERADE
fi
```

> **Rule:** never grep `iptables-save` output for idempotency. Use
> `iptables -C`. If you must parse, expect `/32` suffixes and inserted
> `-m <proto>` module matches.

## 57.5 Bug found: a partial write truncated the script

Applying the first patch with a shell heredoc left
`/usr/local/bin/mc-relay-nat.sh` at **312 bytes** — header comment only, no
executable statements. `bash -n` still passed (comments are valid bash), so a
syntax check alone did not catch it. The systemd unit reported
`Finished` while installing *zero* rules.

**Lesson:** after editing a script over SSH, verify it by **length/line count
and behaviour**, not just `bash -n`. The script was rebuilt to 65 lines and
re-tested for idempotency.

## 57.6 Commands

Rebuild and install the script (written locally, copied over stdin — no
heredoc-quoting hazards):

```bash
bash -n /tmp/mc-relay-nat.sh
ssh root@89.36.162.171 'cat > /usr/local/bin/mc-relay-nat.sh && \
  chmod 755 /usr/local/bin/mc-relay-nat.sh' < /tmp/mc-relay-nat.sh
```

Deduplicate the accumulated MSS clamp rules before the fixed guard takes over:

```bash
while [ "$(iptables -t mangle -L POSTROUTING -n | grep -c TCPMSS)" -gt 1 ]; do
  iptables -t mangle -D POSTROUTING -o wg0 -p tcp --tcp-flags SYN,RST SYN \
    -j TCPMSS --set-mss 1380
done
```

Idempotency proof — run 3x, counts must not move:

```bash
for i in 1 2 3; do
  /usr/local/bin/mc-relay-nat.sh
  echo "run $i -> DNAT=$(iptables -t nat -L PREROUTING -n | grep -c 'DNAT.*10.200.0.2') \
MASQ=$(iptables -t nat -L POSTROUTING -n | grep -c MASQUERADE) \
MSS=$(iptables -t mangle -L POSTROUTING -n | grep -c TCPMSS)"
done
```

```text
run 1 -> DNAT=2 MASQ=1 MSS=1
run 2 -> DNAT=2 MASQ=1 MSS=1
run 3 -> DNAT=2 MASQ=1 MSS=1
```

Start the oneshot so `systemctl is-active` tracks reality (guards make this
safe to re-run):

```bash
systemctl start mc-relay-nat
systemctl is-active  mc-relay-nat   # active
systemctl is-enabled mc-relay-nat   # enabled
```

Final live state:

```text
NAT PREROUTING   1  DNAT tcp dpts:30000:30199 -> 10.200.0.2
NAT PREROUTING   2  DNAT tcp dpt:25565        -> 10.200.0.2:30079
NAT POSTROUTING  1  MASQUERADE -> 10.200.0.2
MANGLE POSTROUTING 1 TCPMSS set 1380
```

## 57.7 `wg-quick@wg0` reports `failed` while the tunnel is fine

```text
wg-quick[950337]: wg-quick: `wg0' already exists
```

The interface was created out-of-band (manually, or by an earlier unit), so
systemd's later `wg-quick up wg0` aborts. The tunnel itself is healthy
(`wg show`: recent handshake, ~1.1 GiB received). The service unit originally
declared `Requires=wg-quick@wg0.service`, so a `failed` dependency blocked the
DNAT oneshot at boot — which is exactly what happened on 2026-08-21
(`Dependency failed for mc-relay-nat.service`).

A drop-in relaxes the hard dependency to an ordering hint, because what matters
is that `wg0` *exists*, not that the unit succeeded:

`/etc/systemd/system/mc-relay-nat.service.d/10-tolerate-wg-unit.conf`

```ini
[Unit]
# wg-quick@wg0 reports failed on this host ("wg0 already exists") even though
# the interface is up and the tunnel works. A hard Requires= therefore makes
# this oneshot fail at boot and the DNAT/MASQ rules never get installed.
# Depend on the interface being present, not on that unit succeeding.
After=wg-quick@wg0.service network-online.target
Wants=network-online.target
```

Effective dependency after the drop-in:

```text
Wants=wg-quick@wg0.service network-online.target
After=wg-quick@wg0.service basic.target ... network-online.target
Requires=sysinit.target system.slice       <- no longer gates on wg-quick
```

`net.ipv4.ip_forward = 1` is persisted in `/etc/sysctl.d/99-wg-relay.conf`, so
forwarding survives reboot independently of the unit ordering.

> **Note:** because `wg-quick@wg0` never actually runs, the tunnel's own
> persistence is *not* proven by that unit being `enabled`. After a real reboot,
> confirm `wg show` has a handshake before assuming the relay works. If it
> turns out `wg0` does not come back, the fix is to stop creating it
> out-of-band and let `wg-quick@wg0` own it — then the drop-in can be dropped
> entirely.

## 57.8 Status

> **Status:** complete. `mc-oompas.42base.com:30080` serves the ATM10SKY
> skyblock world through the Melbicom relay; `:25565` serves the Velocity
> lobby network. Relay rules are idempotent, tracked by systemd, and install
> on boot. Outstanding: an SRV record to let a bare hostname reach port 30080
> (needs a Cloudflare DNS token or a manual dashboard entry), and a
> post-reboot `wg show` check to confirm the tunnel returns on its own.
