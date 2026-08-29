#!/usr/bin/env bash
# Set up OS-level CPU fan control on the HUANANZHI H12D-8D (no BMC module).
#
# What this does:
#   1. Installs the out-of-tree it87 driver (IT8613E Super I/O) via DKMS
#   2. Installs it87-load.service (loads it87 with force_id at boot)
#   3. Installs fancontrol.conf.template + fancontrol-gen.service
#      (regenerates /etc/fancontrol with current hwmon indices at boot —
#       indices swap between boots, so static configs go stale)
#   4. Enables fancontrol.service
#
# Usage:
#   sudo bash scripts/fancontrol/setup-it87.sh          # full setup
#   sudo bash scripts/fancontrol/setup-it87.sh --check  # just verify
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_DIR="$REPO_ROOT/scripts/fancontrol"
IT87_GIT="https://github.com/frankcrawford/it87.git"
# NOTE: clone dir name matters — dkms-install.sh derives the DKMS package name
# from the directory basename, so it MUST be "it87" (not a $$-suffixed tmp name).
IT87_TMP="/tmp/it87"

CHECK=0
[[ "${1:-}" == "--check" ]] && CHECK=1

msg() { echo "==> $*"; }
export DEBIAN_FRONTEND=noninteractive

verify() {
    local ok=1
    msg "Verifying it87 + fancontrol state"
    lsmod | grep -q '^it87' && echo "  OK: it87 loaded" \
        || { echo "  FAIL: it87 not loaded"; ok=0; }
    local chip
    chip=$(grep -l '^it8613$' /sys/class/hwmon/hwmon*/name 2>/dev/null | head -1 || true)
    if [[ -z "$chip" ]]; then
        echo "  FAIL: it8613 hwmon not found"; ok=0
    else
        echo "  OK: it8613 at ${chip%/name}"
        echo "      fan2=$(cat "${chip%/name}/fan2_input") RPM  pwm2=$(cat "${chip%/name}/pwm2")"
    fi
    systemctl is-active fancontrol >/dev/null 2>&1 && echo "  OK: fancontrol active" \
        || { echo "  FAIL: fancontrol not active"; ok=0; }
    [[ $ok -eq 1 ]] && echo "VERIFY OK" || exit 1
}

if [[ $CHECK -eq 1 ]]; then verify; exit 0; fi
if [[ $EUID -ne 0 ]]; then
    echo "Error: run as root (sudo bash $0)" >&2
    exit 1
fi

# --- 1. it87 driver via DKMS ---------------------------------------------------
if ! lsmod | grep -q '^it87'; then
    msg "Installing it87 driver (DKMS)"
    apt-get install -y -qq dkms build-essential "linux-headers-$(uname -r)"
    rm -rf "$IT87_TMP"
    git clone --depth 1 "$IT87_GIT" "$IT87_TMP"
    (cd "$IT87_TMP" && ./dkms-install.sh)
    rm -rf "$IT87_TMP"
else
    msg "it87 module already loaded"
fi

# --- 2. Systemd units ------------------------------------------------------------
msg "Installing systemd units"
install -m 644 "$SRC_DIR/it87-load.service"       /etc/systemd/system/
install -m 644 "$SRC_DIR/fancontrol-gen.service"  /etc/systemd/system/
install -m 755 "$SRC_DIR/generate-fancontrol.sh"  /usr/local/sbin/
install -m 644 "$SRC_DIR/fancontrol.conf.template" /etc/fancontrol.conf.template
systemctl daemon-reload

msg "Loading it87 now"
systemctl enable --now it87-load.service

# --- 3. fancontrol ----------------------------------------------------------------
msg "Installing fancontrol + generating config"
apt-get install -y -qq fancontrol
/usr/local/sbin/generate-fancontrol.sh /etc/fancontrol.conf.template /etc/fancontrol
systemctl enable fancontrol
systemctl restart fancontrol

sleep 5
msg "Verifying"
verify
echo
echo "Monitor:  journalctl -u fancontrol -f"
echo "Tune:     edit $SRC_DIR/fancontrol.conf.template, re-run this script"