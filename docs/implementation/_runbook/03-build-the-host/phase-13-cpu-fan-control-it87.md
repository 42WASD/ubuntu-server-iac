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

The board BIOS (**AMI Aptio Setup Utility**, BIOS 2.20.1275) has its own fan
curve, configured on 2026-10-13 once a monitor was available. Recorded here
because BIOS and OS control **cannot both act at once**.

### Values as set in the BIOS UI

| BIOS field | Value set |
|---|---|
| Fan off temperature limit | 45 |
| Fan start temperature limit | 65 |
| Fan full speed temperature limit | 79 |
| Fan start PWM | 65 |
| PWM slope setting | 4 PWM |

### Values as actually programmed into the IT8613E (ground truth)

The BIOS curve is not opaque — the `it87` driver exposes the auto-point
registers, so the programmed curve can be read back **from the OS**:

```bash
h=$(for d in /sys/class/hwmon/hwmon*; do [ "$(cat $d/name)" = it8613 ] && echo $d; done)
for f in pwm2_auto_point1_temp pwm2_auto_point2_temp pwm2_auto_point3_temp \
         pwm2_auto_start pwm2_auto_slope pwm2_enable; do echo "$f = $(cat $h/$f)"; done
```

```text
pwm2_auto_point1_temp = 45000   -> 45 C   (off limit)
pwm2_auto_point2_temp = 55000   -> 55 C   (start-PWM reached)
pwm2_auto_point3_temp = 79000   -> 79 C   (100% speed)
pwm2_auto_start       = 65      -> 65/255 = 25% duty
pwm2_auto_slope       = 32
pwm2_enable           = 2       -> automatic (hardware) control
```

> **UI vs register discrepancy:** three of the four UI values map 1:1
> (off 45 → point1, full 79 → point3, start PWM 65 → `auto_start`), but the UI
> **start limit 65** is stored as **point2 = 55 °C**. Re-check that field and
> save with F10 — it may not have been applied, or this Aptio build maps it
> elsewhere.

### What "PWM slope = 4" actually means

**It is NOT "4 PWM per °C".** Two pieces of evidence:

1. The UI value **4 is stored as register value 32** (a ×8 scale) — so it is not
   a direct PWM-per-degree step.
2. Deriving the real ramp rate from the three points:
   `(255 − 65) / (79 − 55) = 7.9` PWM/°C ≈ **8 PWM per °C** (~3 % duty per °C).

So the UI "4" corresponds to roughly **8 PWM/°C**, i.e. the unit is about
**2 PWM per °C per UI step** (slope 1 ≈ 2 PWM/°C, slope 4 ≈ 8 PWM/°C; higher =
steeper).

The important structural point: **the three temperature points dominate the
curve shape.** The slope only controls how sharply it climbs between
"start PWM" and "full speed". A 24 °C span (55→79) at 8 PWM/°C gives a long,
gentle ramp.

Linear model between point2 and point3:

| Temp | PWM | Duty |
|---|---|---|
| 55 °C | 65 | 25 % |
| 60 °C | 105 | 41 % |
| 65 °C | 144 | 57 % |
| 70 °C | 184 | 72 % |
| 74 °C | 215 | 84 % |
| 79 °C | 255 | 100 % |

### Empirical check (2026-10-13)

Briefly switching `pwm2` to automatic mode exercised the BIOS curve live:

```bash
echo 2 | sudo tee $h/pwm2_enable    # automatic -> BIOS curve
sleep 25; cat $h/pwm2 $h/fan2_input
echo 1 | sudo tee $h/pwm2_enable    # back to manual
sudo systemctl restart fancontrol   # let fancontrol reclaim the channel
```

```text
BIOS auto @ Tctl 57.1 C  ->  pwm 65 (25%),  2973 RPM
fancontrol @ Tctl 57.8 C ->  pwm 50 (20%),  2376 RPM   (restored)
```

At 57 °C the BIOS curve sat exactly at the start PWM and had **not begun
ramping** — consistent with the ramp being gated at the start limit rather than
at point2 = 55 °C.

> **Always restore afterwards.** Leaving `pwm2_enable=2` hands control to the
> BIOS curve and `fancontrol` will keep writing to a channel it no longer owns.

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
| Start ramping | 65 °C (UI) / 55 °C (reg) | 65 °C (`MINTEMP`) |
| Full speed at | **79 °C** | **74 °C** (`MAXTEMP`) |
| Duty at ramp start | **65/255 ≈ 25%** | 50/255 ≈ 20% |
| Ramp rate | ~8 PWM/°C | linear floor→full over 9 °C |
| Smoothing | none (firmware) | `AVERAGE=4` (~20 s) |
| Poll interval | firmware | 5 s |
| Temp source | board sensor (`temp1`) | `k10temp` **Tctl** |

Sensor correspondence is close on this board — measured **within ~1 °C**
(`temp1` 57.0 °C vs `Tctl` 57.8 °C), so BIOS thresholds transfer directly from
the fancontrol numbers without a fudge factor.

### What differs, and why

1. **Full speed is 5 °C earlier in `fancontrol` (74 vs 79 °C).** The Rome
   **TjMax is ~77 °C** (this part: EPYC 7742, TDP 225 W). The BIOS value of
   **79 °C is *above* TjMax** — the CPU would be throttling before the fan ever
   reached full speed. `fancontrol`'s 74 °C keeps 3 °C of headroom. This is the
   single most important difference and the main reason the OS curve exists.
2. **The BIOS quiet floor starts lower (45 °C off, 55 °C reg start).** On this
   host idle Tctl sits at **57–65 °C**, so the BIOS curve is already part-way
   up the ramp at idle — exactly the noise problem `fancontrol` was tuned to fix
   (`MINTEMP` raised 55→60→65).
3. **The BIOS starts ramping at a slightly higher duty (25% vs 20%).** BIOS
   `Fan start PWM = 65` ≈ 25%; the fan's hardware floor is ~2420 RPM below duty
   50 (`fancontrol` `MINPWM=50` ≈ 20%), so the two floors are close but the BIOS
   one is marginally more aggressive/audible.
4. **Smoothing.** `fancontrol` averages 4 × 5 s polls (~20 s) so short Tctl
   spikes don't cause fan jump-scares. The BIOS curve has no such damping —
   another source of the noise bursts that motivated the OS tuning.
5. **Sensor.** The BIOS uses the board's thermistor (`temp1`); `fancontrol` reads
   `k10temp` **Tctl**. They track within ~1 °C here, but they are not identical.

### Recommended BIOS values (make the fallback safe)

Goal: if `fancontrol` ever fails, the BIOS curve should still be **safe**.
Change only what matters:

| BIOS field | Currently | **Set to** | Why |
|---|---|---|---|
| Fan off temperature limit | 45 | **45** (keep) | harmless; idle sits above it |
| Fan start temperature limit | 65 | **65** (keep) | matches `MINTEMP` |
| **Fan full speed temperature limit** | **79** | **74** ⚠️ | **79 °C is above TjMax (~77 °C)** |
| Fan start PWM | 65 | **50** (or **20** if %) | match the 20 % floor |
| PWM slope setting | 4 | **4** (keep) | ~8 PWM/°C, close enough |

**The one change that genuinely matters is 79 → 74** (use 72 for extra margin).
Everything else is cosmetic.

> **`Fan start PWM` unit caveat:** `fancontrol`'s `50` is out of **255** (= 20 %).
> If the BIOS field is 0–255 use **50**; if it is a percentage use **20**.
> Verify after applying: `sensors | grep fan2` should read **~2400–2700 RPM**
> (the fan's hardware floor). If it lands much higher, the field is a percentage
> — halve the value.

> **Don't chase silence in the BIOS.** There is no `AVERAGE` equivalent, so the
> firmware reacts instantly to spikes. Optimise the fallback for **safety**,
> not quiet.

### At-home checklist

1. Enter BIOS (Aptio; DEL/F2 at POST).
2. Set **Fan full speed temperature limit = 74**.
3. Optionally set **Fan start PWM = 50** (or 20 if the field is a %).
4. Save with **F10**, reboot.
5. Verify from the OS:

   ```bash
   h=$(for d in /sys/class/hwmon/hwmon*; do [ "$(cat $d/name)" = it8613 ] && echo $d; done)
   cat $h/pwm2_auto_point3_temp     # expect 74000
   cat $h/pwm2_auto_start           # expect 50 (or 51 for 20%)
   cat $h/pwm2_enable               # expect 1 -> fancontrol still owns it
   sensors | grep -E 'fan2|pwm2'    # floor ~2400-2700 RPM
   systemctl is-active fancontrol   # active
   ```

6. If the fan sounds wrong, `sudo systemctl restart fancontrol` reclaims the
   channel.

## 13.9 Infra encoding

- `scripts/fancontrol/` — setup script, template, generator, units, README.
- `/etc/modules-load.d/it87.conf` → `it87 force_id=0x8613`
  (also `it87-load.service`).
- `/etc/fancontrol.conf.template` + `/etc/fancontrol` (generated).
- Enabled units: `it87-load.service`, `fancontrol-gen.service`,
  `fancontrol.service`.
- DKMS module `it87/c567739` (frankcrawford fork).
