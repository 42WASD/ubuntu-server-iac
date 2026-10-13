#!/usr/bin/env bash
# Generate /etc/fancontrol at boot with CURRENT hwmon indices.
#
# fancontrol's DEVPATH/DEVNAME pinning is fragile here: the it87 module loads
# asynchronously, so hwmon indices (hwmon1/hwmon2) swap between boots and the
# stock unit fails with "Device path has changed".
#
# This script rewrites the hwmon indices in the template at runtime by
# matching DEVPATH (stable, from readlink) — then fancontrol starts clean.
#
# Usage: generate-fancontrol.sh <template.conf> </etc/fancontrol>
set -euo pipefail

TEMPLATE="${1:?usage: generate-fancontrol.sh <template> <output>}"
OUTPUT="${2:?usage: generate-fancontrol.sh <template> <output>}"

# Map stable device path -> current hwmonN (in fancontrol's format)
declare -A CURPATH=()
for d in /sys/class/hwmon/hwmon*; do
    name=$(cat "$d/name" 2>/dev/null) || continue
    p=$(readlink -f "$d/device" 2>/dev/null | sed 's|^/sys/||')
    # k10temp has no device link; derive from its own path
    [[ -z "$p" ]] && p=$(readlink -f "$d" | sed -e 's|^/sys/||' -e 's|/hwmon/hwmon[0-9]*$||')
    CURPATH["$name"]="$p"
done

resolve() { # resolve <device-name-in-template> -> current hwmonN
    local want="$1"
    for name in "${!CURPATH[@]}"; do
        if [[ "$name" == "$want" ]]; then
            for d in /sys/class/hwmon/hwmon*; do
                [[ "$(cat $d/name 2>/dev/null)" == "$want" ]] && echo "hwmon${d##*hwmon}" && return 0
            done
        fi
    done
    return 1
}

# At boot the hwmon devices may not have finished registering yet, so poll
# briefly instead of failing on the first look. Observed: k10temp is routinely
# missing on the very first attempt, which made fancontrol-gen.service exit 1
# and emit a spurious "Failed to start" on every boot (systemd's restart then
# succeeded). Retrying in-process keeps the unit green.
resolve_retry() { # resolve_retry <device-name> [timeout-seconds]
    local want="$1" timeout="${2:-15}" deadline=$(( SECONDS + ${2:-15} )) val
    while :; do
        if val=$(resolve "$want"); then
            echo "$val"
            return 0
        fi
        if (( SECONDS >= deadline )); then
            echo "ERROR: $want hwmon not found after ${timeout}s" >&2
            return 1
        fi
        sleep 0.5
    done
}

IT87=$(resolve_retry it8613) || exit 1
K10=$(resolve_retry k10temp) || exit 1

echo "it8613=$IT87 k10temp=$K10"

sed -e "s/@IT87@/$IT87/g" -e "s/@K10@/$K10/g" "$TEMPLATE" > "$OUTPUT"
chmod 644 "$OUTPUT"
echo "Generated $OUTPUT"