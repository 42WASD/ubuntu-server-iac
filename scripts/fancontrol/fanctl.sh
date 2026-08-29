#!/usr/bin/env bash
# Manual Supermicro fan control for EPYC 7742 / RTX 3090 host.
#
# Thin wrapper around thirdparty/supermicro-fancontrol/fan-control.sh so the
# tuned profile can be controlled by hand without cd-ing into the submodule.
#
# Usage:
#   scripts/fancontrol/fanctl.sh status              # show zone speeds + mode
#   scripts/fancontrol/fanctl.sh 0 50                # zone 0 (CPU/case) to 50%
#   scripts/fancontrol/fanctl.sh 1 40                # zone 1 (GPU/FANA-B) to 40%
#   scripts/fancontrol/fanctl.sh all 60              # both zones to 60%
#   scripts/fancontrol/fanctl.sh optimal             # back to BMC auto control
#   scripts/fancontrol/fanctl.sh full                # force full speed (manual mode)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAN_CTL="$REPO_ROOT/thirdparty/supermicro-fancontrol/fan-control.sh"

if [[ ! -x "$FAN_CTL" ]]; then
    echo "Error: submodule not populated. Run: git submodule update --init" >&2
    exit 1
fi

if [[ $# -eq 0 ]]; then
    "$FAN_CTL" status
    exit 0
fi

"$FAN_CTL" "$@"