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
| < 65 °C | PWM 50 → fan hardware floor (~2420 RPM, quiet) |
| 65–74 °C | linear ramp |
| ≥ 74 °C | full speed (~6800 RPM), 3 °C under TjMax |

Tuned "quiet for longer": the quiet floor holds to 65 °C (idle Tctl on the
EPYC 7742 sits at 57–65 °C), and the ramp tops out at 74 °C with 3 °C of
headroom under the Rome TjMax (~77 °C, TDP 225 W). Polling is 5 s so the top
of the ramp is responsive, and `AVERAGE=4` smooths the temperature over the
last 4 readings (~20 s) so short Tctl spikes cannot cause sudden fan-speed
jump-scares — sustained load still ramps normally.

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

Expected: quiet floor to ~65 °C; under `stress-ng` CPU load (see the
[System Stress Test](../../../guides/operations/stress-test-guide.md)) Tctl
stabilizes around 66–68 °C with the fan at ~5500–6000 RPM (ramping gradually
thanks to `AVERAGE=4`), and falls back to the floor afterwards.

## If a BMC module is added later

The IPMI path was evaluated and then **removed** (2026-10-13): the fork of
`jvdillon/supermicro-fancontrol` was vendored as a `thirdparty/` submodule but
was never usable on this host (no BMC module → no `/dev/ipmi*`), and was never
installed. The submodule and its wrapper scripts have been deleted. To adopt
IPMI control later, add the BMC SO-DIMM module and re-vendor the upstream
project.

## BIOS vs OS fan control

The board BIOS has its own fan curve. Both cannot be active at once:
`fancontrol` drives `pwm2` in **software/manual** mode (`pwm2_enable=1`), which
overrides the BIOS curve while the OS is running. The BIOS curve therefore only
governs the period before the OS takes over (boot), and would take over again
if `fancontrol` were disabled.

The BIOS curve is **readable from the OS** via the driver's auto-point
registers, so it can be audited rather than guessed:

```bash
h=$(for d in /sys/class/hwmon/hwmon*; do [ "$(cat $d/name)" = it8613 ] && echo $d; done)
cat $h/pwm2_auto_point{1,2,3}_temp $h/pwm2_auto_start $h/pwm2_auto_slope $h/pwm2_enable
```

Key safety rule: the BIOS **full-speed temperature must stay below the CPU's
TjMax** (~77 °C for this Rome EPYC 7742). A BIOS value of 79 °C — above TjMax —
means the CPU throttles before the fan reaches full speed. Keep it at **74 °C**
to match the `fancontrol` curve. Full decode, slope explanation and the at-home
change checklist are in
`_runbook/03-build-the-host/phase-13-cpu-fan-control-it87.md` §13.7–13.8.
