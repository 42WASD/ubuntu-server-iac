# Phase 7 — host firewall

The goal is not:

```text
install nftables
-> flush everything
-> hope Kubernetes survives
```

The goal is:

```text
protect host-facing services
without taking ownership of Cilium's internal networking tables
```

Use a dedicated table.

Create a platform-owned rules file instead of taking ownership of the whole nftables ruleset:

```bash
sudo mkdir -p /etc/nftables.d
sudoedit /etc/nftables.d/host-filter.nft
```

A conservative single-node starting point:

```nft
table inet host_filter {
    chain input {
        type filter hook input priority filter; policy drop;

        ct state established,related accept
        ct state invalid drop

        iifname "lo" accept

        # ICMP / ICMPv6 are useful for MTU, reachability and IPv6 correctness.
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept

        # Tailscale management.
        iifname "tailscale0" tcp dport { 22, 6443, 9345, 10250 } accept

        # Optional: allow LAN SSH temporarily during bootstrap.
        # Replace with your real admin subnet or remove once Tailscale is proven.
        # ip saddr 192.168.1.0/24 tcp dport 22 accept
    }

    chain forward {
        type filter hook forward priority filter; policy accept;
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

Use a dedicated systemd unit which deletes **only our own table** before reloading it:

```bash
sudoedit /etc/systemd/system/platform-nftables.service
```

```ini
[Unit]
Description=Platform host nftables policy
After=network-pre.target
Before=network.target rke2-server.service
Wants=network-pre.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=-/usr/sbin/nft delete table inet host_filter
ExecStart=/usr/sbin/nft -f /etc/nftables.d/host-filter.nft
ExecReload=-/usr/sbin/nft delete table inet host_filter
ExecReload=/usr/sbin/nft -f /etc/nftables.d/host-filter.nft
ExecStop=-/usr/sbin/nft delete table inet host_filter

[Install]
WantedBy=multi-user.target
```

Validate syntax:

```bash
sudo nft -c -f /etc/nftables.d/host-filter.nft
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now platform-nftables.service
```

Inspect:

```bash
sudo nft list table inet host_filter
```

Important:

```text
Never run "nft flush ruleset" as a routine firewall reload after Kubernetes exists.
```

Our automation deletes/recreates only `inet host_filter`, leaving Cilium/Kubernetes-owned networking state alone.

## Why `forward` is not default-drop yet

Cilium/Kubernetes must move Pod traffic.

Host firewall hardening and Pod NetworkPolicy are different layers.

Do not break forwarding first and attempt to debug Cilium afterward.

## Checkpoint 6

Verify:

```text
Tailscale SSH works
Internet outbound works
DNS works
apt update works
```

Then reboot once:

```bash
sudo reboot
```

After reboot, verify again.

---
