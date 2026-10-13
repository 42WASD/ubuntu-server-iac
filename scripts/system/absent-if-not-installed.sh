#!/usr/bin/env bash
# Print "absent" if a dpkg package is not installed, "present" if it is.
# Used by the doc-impact live-expectations probes (command engine splits on
# whitespace, so a one-liner with nested quoting can't be expressed inline).
#
# Usage: absent-if-not-installed.sh <package-name>
set -u
pkg="${1:?usage: absent-if-not-installed.sh <package-name>}"
if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q '^install ok installed$'; then
    echo present
else
    echo absent
fi
