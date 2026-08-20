---
phase: 03-build-the-host/12-16-phase-7-host-firewall
---
# Phase 7 — host firewall (LEARN mode + approval tooling)

**Intent:** bring up a platform-owned host firewall that is safe by default —
it accepts all traffic and LOGS new inbound connections (so we learn which
ports are actually used and never accidentally break Tailscale), plus a simple
"option 2" approval helper to manage ports.

> This is deliberately NOT a default-drop policy yet. LEARN mode keeps
> everything working while we observe real traffic. Tightening to default-drop
> comes later by moving approved ports into the ruleset and setting `policy drop`.

## 7.1 Design (accept + log, learn mode)

Host firewall is a dedicated nftables table `inet host_filter`, owned by a
systemd service that only ever deletes/reloads our own table (never a full
`nft flush ruleset`), so Cilium/Kubernetes tables are left alone.

Rules:
- `policy accept` on input/forward/output (LEARN mode — nothing blocked)
- `ct state invalid drop` (safe hygiene)
- `iifname "lo" accept`, `ct state established,related accept`
- `ct state new log prefix "HOST-NEW " limit rate 5/second accept`
  → every new inbound connection is logged to the kernel journal with its
  source/dest/proto/ports, so we see what is in use.

Files (source of truth in `scripts/firewall/`):
- `host-filter.nft` — the ruleset (includes `approved-ports.nft`)
- `approved-ports.nft` — permanent allow rules (managed by the tool)
- `platform-nftables.service` — loads/reloads only our table
- `platform-allow-timeout.{service,timer}` — cleanup for one-time allows
- `firewall-approval.sh` — the approval tool

## 7.2 Deploy

```bash
# ruleset + approved list
sudo mkdir -p /etc/nftables.d
sudo cp scripts/firewall/host-filter.nft        /etc/nftables.d/
sudo cp scripts/firewall/approved-ports.nft     /etc/nftables.d/

# systemd units
sudo cp scripts/firewall/platform-nftables.service \
        scripts/firewall/platform-allow-timeout.service \
        scripts/firewall/platform-allow-timeout.timer \
        /etc/systemd/system/

# approval tool
sudo install -m 0755 scripts/firewall/firewall-approval.sh /usr/local/bin/firewall-approval

sudo systemctl daemon-reload
sudo systemctl enable --now platform-nftables.service
sudo systemctl enable --now platform-allow-timeout.timer
```

Syntax was validated first: `nft -c -f host-filter.nft` (only the sandbox
`cache initialization` netlink warning; the em-dash/backtick chars in the
approved file caused a real syntax error and were replaced with ASCII).

## 7.3 Verify

```bash
systemctl is-active platform-nftables.service   # -> active
systemctl is-active platform-allow-timeout.timer # -> active
sudo nft list table inet host_filter             # shows the ruleset
```

**Observed live ruleset (abridged):**
```
table inet host_filter {
  chain input { policy accept;
    ct state invalid drop
    iifname "lo" accept
    ct state established,related accept
    ct state new log prefix "HOST-NEW " limit rate 5/second accept
  }
  chain forward { policy accept; }
  chain output  { policy accept; }
}
```

## 7.4 Approval tool (`firewall-approval`)

`watch` tails journald and prints every `HOST-NEW` inbound, so the admin sees
what is being used (and nothing is ever accidentally blocked):
```bash
sudo firewall-approval watch
```

Permanent allow of a port (appends to `approved-ports.nft` + reloads):
```bash
sudo firewall-approval allow 5432 tcp
```

One-time allow (inserts a rule; `platform-allow-timeout.timer` cleans it up):
```bash
sudo firewall-approval allow-once 9000 tcp
```

## 7.5 What we observed

- First `HOST-NEW` entry already captured (a DHCPv6 solicitation: `SPT=547
  DPT=546` on `enp193s0`) — logging works.
- `allow 9999` inserted `tcp dport 9999 accept`; removed from file + reload
  cleared it (idempotent, clean state restored).
- Tailscale traffic continues to flow (policy accept; LEARN mode).

**Infra encoding:** `infra/ansible/roles/firewall/` — populate `tasks/main.yml`
with the file-deploy + systemd-enable tasks (templates for `.nft` + units),
`defaults/main.yml` with the allow-list. Next step toward default-drop.