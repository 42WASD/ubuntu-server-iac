#!/usr/bin/env bash
# Print "absent" if a snap is not installed, "present" if it is.
# Used by the doc-impact live-expectations probes (command engine splits on
# whitespace, so a one-liner with nested quoting can't be expressed inline).
#
# Usage: absent-if-not-snap.sh <snap-name>
set -u
snap_name="${1:?usage: absent-if-not-snap.sh <snap-name>}"
if snap list "$snap_name" >/dev/null 2>&1; then
    echo present
else
    echo absent
fi
