---
phase: 03-build-the-host/cpu-fan-control-it87
---

# Phase 13 — CPU fan control via it87 (no BMC module)

**Intent:** quiet CPU fan at idle, full speed under stress, entirely from the
OS. The HUANANZHI H12D-8D (`alpha`) shipped **without the optional BMC
module**, so IPMI fan control (and the vendored
`42WASD/supermicro-fancontrol` daemon in `thirdparty/`) is not usable.
Control is instead provided by the **ITE IT8613E** Super I/O chip via the
out-of-tree `it87` driver + `fancontrol`.

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

## 13.6 Parked: IPMI daemon (pending BMC module)

`scripts/fancontrol/fan-daemon.service`, `install.sh`, `fanctl.sh` and the
`thirdparty/supermicro-fancontrol` submodule implement IPMI-based control for
the **forked Supermicro daemon** (CPU-only curve tuned for the 7742). They are
**unused until the optional AST2500 BMC module is installed**; the daemon
validated cleanly against curve-spec parsing (zones `[0,1]` detected) but
cannot reach a BMC. If the module is ever added: install it, then
`sudo bash scripts/fancontrol/install.sh`.

## 13.7 Infra encoding

- `scripts/fancontrol/` — setup script, template, generator, units, README.
- `/etc/modules-load.d/it87.conf` → `it87 force_id=0x8613`
  (also `it87-load.service`).
- `/etc/fancontrol.conf.template` + `/etc/fancontrol` (generated).
- Enabled units: `it87-load.service`, `fancontrol-gen.service`,
  `fancontrol.service`.
- DKMS module `it87/c567739` (frankcrawford fork).
