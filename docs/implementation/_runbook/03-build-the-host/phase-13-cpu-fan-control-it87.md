---
phase: 03-build-the-host/cpu-fan-control-it87
---

# Phase 13 — CPU fan control via it87 (no BMC module)

**Intent:** quiet CPU fan at idle, full speed under stress, entirely from the
OS. The HUANANZHI H12D-8D (`alpha`) shipped **without the optional BMC
module**, so IPMI fan control is not usable. Control is instead provided by the
**ITE IT8613E** Super I/O chip via the out-of-tree `it87` driver +
`fancontrol`.

## 13.1 Hardware findings (recorded so they are not re-derived)

- DMI: `HUANANZHI H12D-8D V2.0`, AMI BIOS 2.2 (NOT Supermicro — the model
  number is coincidental; `sudo dmidecode -t 2`).
- BMC is an optional AST2500 SO-DIMM card, **not installed**: no `/dev/ipmi*`,
  `ipmi_si` finds no KCS interface even with forced ports 0xCA2/0xCA9
  ("Interface detection failed").
- `sensors-detect` probe found: `ITE IT8613E Super IO Sensors` at ISA 0xA30,
  driver "to-be-written" (in-tree kernel lacks the chip).
- Out-of-tree driver: <https://github.com/frankcrawford/it87> (supports
  IT8613E via `force_id=0x8613`).

```bash
# Probe that identified the chip
yes | sudo sensors-detect | grep -i "ITE\|Super IO"
#   Found `ITE IT8613E Super IO Sensors'  (address 0xa30, driver `to-be-written')
```

## 13.2 Driver install (DKMS)

```bash
sudo apt-get install -y dkms build-essential linux-headers-$(uname -r)
git clone --depth 1 https://github.com/frankcrawford/it87.git /tmp/it87
cd /tmp/it87 && sudo ./dkms-install.sh
sudo modprobe it87 force_id=0x8613
```

> The clone directory MUST be named `it87` — `dkms-install.sh` derives the
> DKMS package name from the basename.

Exposed hwmon (verified): `it8613` at `/sys/devices/platform/it87.2608` with
`pwm2` = CPU fan header (tach `fan2`), and `pwm3`/`pwm5` = unused headers
(no fans connected / BMC-gated SYS headers).

## 13.3 PWM mapping & stall floor (measured)

```bash
d=/sys/class/hwmon/$(grep -l '^it8613$' /sys/class/hwmon/hwmon*/name)
echo 1 | sudo tee $d/pwm2_enable           # manual mode
for v in 70 60 50 40 30 20 15; do
  echo $v | sudo tee $d/pwm2; sleep 3; cat $d/fan2_input
done
# pwm<=50 plateaus at ~2420 RPM  -> hardware floor; MINPWM/MINSTOP = 50
```

## 13.4 fancontrol (boot-order-proof config)

hwmon indices for `it8613`/`k10temp` **swap between boots** (it87 loads
asynchronously), which breaks fancontrol's static `DEVPATH` pinning. The repo
therefore installs a template + boot-time generator:

- `scripts/fancontrol/fancontrol.conf.template` — curve with `@IT87@`/`@K10@`
  placeholders.
- `scripts/fancontrol/generate-fancontrol.sh` — resolves current indices into
  `/etc/fancontrol`.
- `it87-load.service` — `modprobe it87 force_id=0x8613` at boot.
- `fancontrol-gen.service` — runs the generator before `fancontrol.service`.

Curve (EPYC 7742, Rome, TjMax ~77 °C, TDP 225 W): idle <65 °C → pwm 50
(floor ~2420 RPM); ramp 65–74 °C; full speed ≥74 °C; `INTERVAL=5`;
`AVERAGE=4` smooths Tctl over ~20 s so short spikes don't trigger fan
jump-scares. `MINSTOP >= MINPWM` is a fancontrol validation constraint
(both = 50).

```bash
sudo bash scripts/fancontrol/setup-it87.sh            # install everything
sudo bash scripts/fancontrol/setup-it87.sh --check    # verify
```

## 13.5 Verification (live)

Quiet floor: **holds to 65 °C** with the tuned curve — Tctl 64.8 °C → 2410
RPM @ pwm 50 (before re-tune, 61.4 °C was already creeping up the ramp).
CPU stress (`stress-ng --cpu $(nproc) --cpu-method matrixprod`, per
`docs/guides/operations/stress-test-guide.md`): Tctl stabilizes at 66–68 °C →
fan ~5500–6000 RPM @ pwm 148–174; on cool-down it returns to the floor.

```bash
# Observed during 45 s CPU-only stress + fan sampling (tuned curve)
stress-ng --cpu $(nproc) --cpu-method matrixprod --timeout 45s --quiet &
# t+5s: Tctl 68C -> fan 5578 RPM pwm 159
# t+40s: Tctl 67C -> fan 5973 RPM pwm 174 (equilibrium)
```

Re-tune 2026-08-31 (anti "jump-scare"): quiet floor raised 60→65 °C and
`AVERAGE=4` added. Verified: Tctl 64.8 °C → 2410 RPM (floor holds); during a
45 s stress burst the ramp is gradual — pwm 82 @ ~3426 RPM at t+15s, pwm 169
@ ~5818 RPM at t+30s — no instant burst; cool-down returns to the floor.

### 2026-09-07 outage: fancontrol dead after reboot (hwmon drift)

Cause of the reboot itself (traced via journal + unattended-upgrades log):
on 2026-09-06 06:05 UTC `unattended-upgrades` installed a new kernel
(`linux-image-generic`), found `/var/run/reboot-required`, and — per
`Automatic-Reboot "true"` / `Automatic-Reboot-Time "03:00"` in
`/etc/apt/apt.conf.d/50unattended-upgrades` — scheduled a clean reboot for
03:00 UTC, executed via logind countdown. Not a crash or power loss. The
it87 DKMS module built fine against the new kernel; the reboot simply
exposed the missing `fancontrol-gen` enablement below. **Aftermath:** this
incident drove the platform-wide decision to disable automatic reboots
entirely (`Automatic-Reboot "false"`, Phase 2.1 runbook + `base` role) —
on a single-node platform an unchosen reboot is a full-cluster outage.

Host rebooted 03:04 UTC; hwmon indices swapped (it8613→hwmon1, k10temp→hwmon2)
and `fancontrol` crash-looped on the stale `DEVPATH` pinning ("Device path has
changed", restart counter 5 → failed). Root cause: **`fancontrol-gen.service`
was installed but never enabled** — `setup-it87.sh` only installed it, so the
boot-time regeneration that exists precisely for this never ran. Fans ran
unmanaged at ~5357 RPM until manual recovery.

```bash
# Recovery (regenerate with current indices + restart):
sudo /usr/local/sbin/generate-fancontrol.sh /etc/fancontrol.conf.template /etc/fancontrol
sudo systemctl restart fancontrol
# Fix: enable the generator so future reboots self-heal
sudo systemctl enable fancontrol-gen.service
```

Verified post-fix: `active`, tuned curve loaded (MINTEMP=65, AVERAGE=4),
Tctl 55.4 °C → 2428 RPM floor. `setup-it87.sh` now enables
`fancontrol-gen.service` and `verify --check` asserts it.

## 13.6 Removed: IPMI daemon + thirdparty submodule (2026-10-13)

The IPMI path was evaluated and then **removed entirely**. It had been vendored
as a `thirdparty/supermicro-fancontrol` submodule (fork of
`jvdillon/supermicro-fancontrol`) with wrapper scripts
(`fan-daemon.service`, `install.sh`, `fanctl.sh`) implementing a CPU-only curve
for the 7742. It was **never usable** on this host — no BMC module means no
`/dev/ipmi*` — and was **never installed** (verified: `fan-daemon` service
`not-found`, no `/usr/local/bin/fan-daemon.py`).

Deleted on 2026-10-13:

```bash
git submodule deinit -f thirdparty/supermicro-fancontrol
git rm -f thirdparty/supermicro-fancontrol
git rm scripts/fancontrol/{install.sh,fanctl.sh,fan-daemon.service}
# .gitmodules removed (it only held this one submodule)
# the 42WASD/supermicro-fancontrol fork was deleted from the org
```

If the optional AST2500 BMC module is ever installed, re-vendor the upstream
project and re-add an IPMI control path — nothing is parked in-tree now.

## 13.7 BIOS fan curve (board firmware)

The board BIOS has its own fan curve, configured on 2026-10-13 once a monitor
was available. Recorded here because BIOS and OS control **cannot both act at
once**:

| BIOS setting | Value |
|---|---|
| Fan off temperature limit | 45 |
| Fan start temperature limit | 65 |
| Fan full speed temperature limit | 79 |
| Fan start PWM | 65 |
| PWM slope setting | 4 PWM |

See §13.8 for how this compares to the `fancontrol` curve and why it is
currently **overridden** by the OS.

## 13.8 BIOS curve vs the fancontrol curve

**Which one is active?** `fancontrol`, while the OS is running. `fancontrol`
drives `pwm2` in **software/manual** mode:

```bash
$ cat /sys/class/hwmon/hwmon3/pwm2_enable
1                     # 1 = manual/software; >=2 = automatic (hardware) control
$ sensors | grep pwm2
pwm2:  25%  (freq = 23437 Hz)  MANUAL CONTROL
```

Setting `pwm2_enable=1` hands the channel to software, so the **BIOS curve is
overridden** for as long as `fancontrol` runs. The BIOS curve governs only the
window before the OS service starts (boot) — and would take over again if
`fancontrol` were disabled/stopped.

### Side-by-side

| Aspect | BIOS curve | `fancontrol` curve |
|---|---|---|
| Off / stop below | 45 °C | 65 °C (`MINTEMP`) |
| Start ramping | 65 °C | 65 °C (`MINTEMP`) |
| Full speed at | **79 °C** | **74 °C** (`MAXTEMP`) |
| Duty at ramp start | **65/255 ≈ 25%** (`MINPWM=65`) | 50/255 ≈ 20% (`MINPWM=50`) |
| Ramp shape | **4 PWM** slope setting | linear floor→full |
| Smoothing | none (firmware) | `AVERAGE=4` (~20 s) |
| Poll interval | firmware | 5 s |
| Temp source | board sensor | `k10temp` **Tctl** |

### What differs, and why

1. **Full speed is 5 °C earlier in `fancontrol` (74 vs 79 °C).** The Rome
   **TjMax is ~77 °C** (this part: EPYC 7742, TDP 225 W). The BIOS value of
   **79 °C is *above* TjMax** — the CPU would be throttling before the fan ever
   reached full speed. `fancontrol`'s 74 °C keeps 3 °C of headroom. This is the
   single most important difference and the main reason the OS curve exists.
2. **The quiet floor is much lower in the BIOS (45 vs 65 °C).** With the BIOS
   curve the fan stays at/near stop until 45 °C. On this host idle Tctl sits at
   **57–65 °C**, so the BIOS curve would already be **ramping at idle** — which
   is exactly the noise problem `fancontrol` was tuned to fix.
3. **The BIOS starts ramping at a slightly higher duty (25% vs 20%).** BIOS
   `Fan start PWM = 65` ≈ 25% duty; the fan's hardware floor is ~2420 RPM below
   duty 50 (`fancontrol` `MINPWM=50` ≈ 20%), so the two floors are close but the
   BIOS one is marginally more aggressive/audible.
4. **Smoothing.** `fancontrol` averages 4 × 5 s polls (~20 s) so short Tctl
   spikes don't cause fan jump-scares. The BIOS curve has no such damping —
   another source of the noise bursts that motivated the OS tuning.
5. **Sensor.** The BIOS uses the board's own thermal sensor; `fancontrol` reads
   `k10temp` **Tctl**, the CPU's authoritative junction temperature. These are
   not the same number, so the two curves are not directly comparable at the
   same displayed temperature.

### Recommendation

Leave `fancontrol` as the active controller — it is strictly safer (full speed
below TjMax) and quieter (floor held to 65 °C). Keep the BIOS curve only as the
pre-OS fallback; the values recorded above are fine for that role. If you ever
disable `fancontrol`, be aware the BIOS curve will resume and its 79 °C full-speed
point is **above TjMax**.

## 13.9 Infra encoding

- `scripts/fancontrol/` — setup script, template, generator, units, README.
- `/etc/modules-load.d/it87.conf` → `it87 force_id=0x8613`
  (also `it87-load.service`).
- `/etc/fancontrol.conf.template` + `/etc/fancontrol` (generated).
- Enabled units: `it87-load.service`, `fancontrol-gen.service`,
  `fancontrol.service`.
- DKMS module `it87/c567739` (frankcrawford fork).
