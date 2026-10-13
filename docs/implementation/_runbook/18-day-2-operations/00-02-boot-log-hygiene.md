---
phase: 18-day-2-operations/boot-log-hygiene
---

# Runbook — boot-log hygiene (wekan, openipmi, it87.conf, networkd/NM, fancontrol)

A 2026-10-13 audit of `journalctl` + rsyslog archives on `alpha` found five
sources of boot noise and two real bugs. All are now fixed; this page records
what they were and how each was resolved.

## 1. Wekan snap — removed

- **What it was:** a Kanban board (`wekan` snap, rev 11.36) installed 2026-08-17.
- **Why it was a problem:** it never started. `wekan-control` died instantly on
  `line 471: WRITABLE_PATH: unbound variable` (a `set -u` + unset-variable bug in
  the snap itself). The Wekan app (port 3001) never ran; only FerretDB listened.
  It crash-looped ~4,900 times, emitting **~84.6% of the journal** (~897k lines
  per boot, ~184 lines per restart, ~400 MB of syslog in 15.5 h).
- **Dependencies:** none. Not in the IaC, the Cloudflare tunnel, or the cluster.
- **Fix:** `snap stop --disable wekan`, then `snap remove --purge wekan`. The
  crash loop had a pending `service-control` change that blocked plain
  `snap remove`; stopping the service first was required.
- **Verification:** `snap list wekan` → not found; `/var/snap/wekan` gone;
  `systemctl --failed` empty; journal rate dropped from 2,600 → 1,197 lines/2 min.

## 2. `openipmi` — removed

- **What it was:** the SysV `openipmi` package, trying to load IPMI drivers.
- **Why it was a problem:** this board has **no BMC** (the optional AST2500
  SO-DIMM module is not installed). The unit failed on every boot and logged
  ~29k deprecation warnings per boot.
- **Fix:** `apt-get remove --purge openipmi`. Nothing depended on it; the
  `ipmievd.service` unit (from `ipmitool`) is disabled and harmless.
- **Verification:** `systemctl --failed` no longer lists it.

## 3. `/etc/modules-load.d/it87.conf` — deleted

- **What it was:** a hand-created file containing `it87 force_id=0x8613`.
- **Why it was a problem:** `modules-load.d` takes **bare module names only** —
  no arguments. The whole line was read as one module named `it87 force_id=0x8613`,
  producing `Failed to find module 'it87 force_id=0x8613'` twice every boot.
- **Why harmless:** `it87-load.service` loads the module correctly with
  `modprobe it87 force_id=0x8613`; the file was redundant.
- **Fix:** `rm /etc/modules-load.d/it87.conf`.
- **Note:** not created by `scripts/fancontrol/setup-it87.sh` (that uses the
  systemd unit). Do not recreate it.

## 4. `fancontrol-gen.service` boot race — fixed in the repo

- **What it was:** `generate-fancontrol.sh` failed on the **first** attempt at
  every boot with `ERROR: k10temp hwmon not found`. systemd's restart then
  succeeded, so the unit looked green but logged a spurious failure.
- **Fix:**
  - `generate-fancontrol.sh` now polls for the hwmon devices (0.5 s interval,
    15 s budget) instead of failing on the first look.
  - `fancontrol-gen.service` has `TimeoutStartSec=60` to cover that window.
  - New drop-in `scripts/fancontrol/fancontrol.service.d/10-order.conf` adds
    `Requires=fancontrol-gen.service` + `After=fancontrol-gen.service`, so
    `fancontrol` cannot start against a stale config if the generator fails.
- **Install:** `setup-it87.sh` now installs the drop-in automatically.
- **Verification:** `systemctl show fancontrol.service -p Requires -p After`
  lists `fancontrol-gen.service`; `systemctl cat fancontrol.service` shows the
  drop-in.

## 5. systemd-networkd vs NetworkManager — fight stopped

- **What it was:** a `Foreign process 'NetworkManager[…]' changed sysctl
  '/proc/sys/net/ipv6/conf/wlx6083e75da3bf/disable_ipv6' from '0' to '1'`
  warning on every boot. networkd forces `0` for interfaces it configures;
  NetworkManager forces `1` for a WiFi device with no connection. They fought
  over the USB WiFi dongle.
- **Root cause:** the dracut fallback `/run/systemd/network/zzzz-dracut-default.network`
  matches **all** interfaces (`Kind=!* Type=!loopback`), so networkd was
  configuring an interface it should never have touched.
- **Fix:**
  - `/etc/systemd/network/zzzz-dracut-default.network` — same name as the
    `/run` file, so it **overrides** it (later path wins). Declares the dongle
    `unmanaged` under `[Link]` (not `[Network]` — that section silently ignores
    the key with `Unknown key 'Unmanaged' in section [Network], ignoring.`).
  - `/etc/sysctl.d/60-wifi-ipv6-off.conf` — pins
    `net.ipv6.conf.wlx6083e75da3bf.disable_ipv6 = 0` so both managers land on
    the same value.
- **Important:** the sysctl is set to `0` (IPv6 **on**), not `1`, because that
  is the value networkd actually enforces. Setting it to `1` makes networkd
  fight back. The goal was to stop the fight, not to disable IPv6 on an
  interface that has no carrier anyway.
- **Verification:** `networkctl list` shows the dongle as `unmanaged`; an 8 s
  link-cycle stress test produced **zero** `Foreign process` messages; ethernet
  is untouched.

## Remaining noise (intentional, not fixed)

- `Sysctl monitor BPF returned error: Invalid argument` — networkd's eBPF
  monitor can't load in this kernel; it falls back to polling. Cosmetic.
- `networkd-dispatcher` `Interface "tmpXXXX" not found` — k8s/LXC create and
  destroy virtual interfaces faster than the dispatcher can query them.
  Harmless race.
- nftables LEARN mode (`/etc/nftables.d/host-filter.nft`) logs every NEW inbound
  connection (~14k kern.log lines/boot). This is the current policy and should
  be tightened to default-drop in a later phase, not silenced ad hoc.
