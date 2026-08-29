# CPU fan control via it87

Quiet-idle / full-under-load CPU fan control **without IPMI**. Applies to
hosts whose BMC is an optional module and was not installed (this board:
HUANANZHI H12D-8D — the BMC is an AST2500 SO-DIMM card; the fan headers
besides `CPU_FAN` also require it).

## Identify the fan controller

```bash
yes | sudo sensors-detect
# Look for: Found `ITE IT8613E Super IO Sensors' (driver `to-be-written')
```

`to-be-written` means the in-tree kernel has no driver for the chip — use the
out-of-tree [it87](https://github.com/frankcrawford/it87) driver (supports the
IT8613E via `force_id=0x8613`).

## Install

```bash
sudo bash scripts/fancontrol/setup-it87.sh
sudo bash scripts/fancontrol/setup-it87.sh --check
```

This builds the `it87` DKMS module, installs two boot units
(`it87-load.service`, `fancontrol-gen.service`) and enables
`fancontrol.service` with a tuned EPYC 7742 curve.

## Curve design

| Band | Behavior |
|------|----------|
| < 60 °C | PWM 50 → fan hardware floor (~2420 RPM, quiet) |
| 60–74 °C | linear ramp |
| ≥ 74 °C | full speed (~6800 RPM), 3 °C under TjMax |

Tuned "quiet for longer": the quiet floor holds to 60 °C (the EPYC 7742 idles
in the high-50s), and the ramp tops out at 74 °C with 3 °C of headroom under
the Rome TjMax (~77 °C, TDP 225 W). Polling is 5 s so the top of the ramp is
responsive.

Constraints learned on this hardware:

- `MINPWM`/`MINSTOP` = 50: below duty 50 the fan plateaus at ~2420 RPM.
- `MINSTOP >= MINPWM` is enforced by `fancontrol`.
- hwmon indices for `it8613`/`k10temp` swap between boots, so the config is
  **generated at boot** from `fancontrol.conf.template` by
  `generate-fancontrol.sh` (static configs go stale).

## Verify

```bash
systemctl status fancontrol
journalctl -u fancontrol -f
sensors   # it8613 shows fan2 RPM + pwm2 under your load
```

Expected: quiet floor to ~60 °C; under `stress-ng` CPU load (see the
[System Stress Test](../../../guides/operations/stress-test-guide.md)) Tctl
stabilizes around 66–68 °C with the fan at ~5500–6000 RPM, and falls back to
the floor afterwards.

## If a BMC module is added later

The IPMI path is prepared but parked: `scripts/fancontrol/install.sh` +
`fan-daemon.service` (forked Supermicro daemon, CPU-only curve). The
`thirdparty/supermicro-fancontrol` submodule documents the IPMI raw commands.
