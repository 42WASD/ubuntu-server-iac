#!/usr/bin/env bash
# Print total usable RAM in whole GiB (integer), for the doc-impact probe.
#
# The doc-impact probe engine runs commands with a naive whitespace split (no
# shell), so probes cannot use quoting or pipes. This helper exists so the
# live-expectations entry can be a simple `bash scripts/system/mem-total-gib.sh`.
#
# Expected on alpha: 123  (8 × 16 GiB installed = 128 GiB; ~123 GiB usable)
set -euo pipefail
awk '/^MemTotal:/ { printf "%d\n", $2 / 1048576 }' /proc/meminfo
