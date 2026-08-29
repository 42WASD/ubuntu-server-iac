# Fan Control — EPYC 7742 CPU profile (ITE IT8613E, no BMC)

OS-level **CPU fan control** for the HUANANZHI H12D-8D (`alpha`), which has
**no BMC module installed** — so IPMI is unavailable and the IT8613E Super I/O
chip is the only fan control surface exposed to the OS.

## Why this approach

- The board's IPMI/BMC is an **optional SO-DIMM module** (AST2500) that was
  **not installed** — `ipmitool` has no local `/dev/ipmi*` device, and
  `ipmi_si` finds no KCS interface (verified: even forcing ports 0xCA2/0xCA9
  fails).
- Without the BMC, the **ITE IT8613E** Super I/O chip (ISA 0xA30) controls the
  CPU fan header. The in-tree kernel has no driver for it ("to-be-written"),
  so we use the out-of-tree **[it87](https://github.com/frankcrawford/it87)**
  driver via DKMS with `force_id=0x8613`.
- PWM control verified live: pwm2 = CPU fan (fan2 tach), fan hardware floor
  ~2420 RPM below duty 50.

## Curve (EPYC 7742, TjMax ~77°C)

| Band | Behavior |
|------|----------|
| < 60°C | PWM 50 → fan floor **~2420 RPM** (quiet idle) |
| 60–74°C | Linear ramp floor → full |
| ≥ 74°C | PWM 255 → **~6800 RPM** (full cooling) |

Tuned "quiet for longer": the floor holds to 60°C and full speed engages at
74°C (3°C under TjMax). Polling is 5 s. Verified live: idle 57°C/2419 RPM;
CPU stress Tctl 66–68°C at ~5500–6000 RPM; cool-down returns to the floor.

### What PWM means here

`pwm2` (0–255) is the **duty cycle of the 4-wire fan's control signal** the
ITE IT8613E sends to the CPU fan: roughly `pwm2/2.55` = percent of full 12 V
pulses. 50 ≈ 20% duty (this fan's spin floor, ~2420 RPM), 255 = 100% duty.

## Files

| File | Purpose |
|------|---------|
| `setup-it87.sh` | One-shot installer (DKMS it87 + units + fancontrol) |
| `fancontrol.conf.template` | Curve template (`@IT87@`/`@K10@` resolved at boot) |
| `generate-fancontrol.sh` | Rewrites hwmon indices into the template at boot |
| `it87-load.service` | Loads it87 with `force_id=0x8613` at boot |
| `fancontrol-gen.service` | Regenerates `/etc/fancontrol` before fancontrol starts |
| `fan-daemon.service`, `install.sh`, `fanctl.sh` | IPMI/BMC daemon (UNUSED — parked until a BMC module is installed) |

## Install

```bash
sudo bash scripts/fancontrol/setup-it87.sh
sudo bash scripts/fancontrol/setup-it87.sh --check   # verify
```

## Manage

```bash
journalctl -u fancontrol -f              # monitor regulation
systemctl status fancontrol
sensors                                  # temps/RPM/pwm readout
```

Tune: edit `fancontrol.conf.template` (MINTEMP/MAXTEMP/MINPWM/MINSTOP), then
re-run `setup-it87.sh` (or regenerate + restart manually).

## Boot chain

`it87-load.service` (loads driver) → `fancontrol-gen.service` (resolves
hwmon indices → `/etc/fancontrol`) → `fancontrol.service` (regulates).

The generator exists because **hwmon indices swap between boots** (it87 loads
asynchronously), which breaks fancontrol's stock `DEVPATH` pinning.