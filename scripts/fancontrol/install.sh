#!/usr/bin/env bash
# Install/update the tuned Supermicro fan control daemon on this host.
#
# Fetches the daemon from the vendored fork (thirdparty/) and installs:
#   1. The tuned systemd unit  -> /etc/systemd/system/fan-daemon.service
#   2. ipmitool + deps         -> apt
#   3. IPMI kernel modules
#   4. Fan low-RPM alarm fix   (if setup-ipmi-limits.sh present)
#
# Usage:
#   sudo bash scripts/fancontrol/install.sh      # install + enable + start
#   sudo bash scripts/fancontrol/install.sh --no-start   # install but don't start
#
# Prereq: the submodule must be populated:
#   git submodule update --init thirdparty/supermicro-fancontrol

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FORK_DIR="$REPO_ROOT/thirdparty/supermicro-fancontrol"
UNIT_SRC="$REPO_ROOT/scripts/fancontrol/fan-daemon.service"
UNIT_DST="/etc/systemd/system/fan-daemon.service"
DAEMON_DST="/usr/local/bin/fan-daemon.py"
SERVICE="fan-daemon"

START=1
if [[ "${1:-}" == "--no-start" ]]; then
    START=0
fi

# --- 0. Preconditions -------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    echo "Error: run as root (sudo bash $0)" >&2
    exit 1
fi
if [[ ! -f "$FORK_DIR/fan-daemon.py" ]]; then
    echo "Error: submodule not populated. Run:" >&2
    echo "  git submodule update --init $FORK_DIR" >&2
    exit 1
fi

# --- 1. Dependencies --------------------------------------------------------
echo "==> Installing ipmitool (IPMI fan control)"
apt-get update -qq
apt-get install -y -qq ipmitool smartmontools nvme-cli

# --- 2. IPMI kernel modules -------------------------------------------------
echo "==> Loading IPMI kernel modules"
modprobe ipmi_msghandler ipmi_si ipmi_devintf 2>/dev/null || true
# Persist across reboots
grep -q '^ipmi_msghandler' /etc/modules 2>/dev/null || echo "ipmi_msghandler" >> /etc/modules
grep -q '^ipmi_si'          /etc/modules 2>/dev/null || echo "ipmi_si"          >> /etc/modules
grep -q '^ipmi_devintf'     /etc/modules 2>/dev/null || echo "ipmi_devintf"     >> /etc/modules

# --- 3. Daemon binary -------------------------------------------------------
echo "==> Installing fan-daemon.py -> $DAEMON_DST"
install -m 755 "$FORK_DIR/fan-daemon.py" "$DAEMON_DST"
if [[ -f "$FORK_DIR/sensors.py" ]]; then
    install -m 644 "$FORK_DIR/sensors.py" /usr/local/lib/python3/dist-packages/ 2>/dev/null \
        || install -m 644 "$FORK_DIR/sensors.py" /usr/lib/python3/dist-packages/
fi

# --- 4. Tuned systemd unit ---------------------------------------------------
echo "==> Installing $UNIT_DST"
install -m 644 "$UNIT_SRC" "$UNIT_DST"
systemctl daemon-reload

# --- 5. Low-RPM alarm fix (best effort) ---------------------------------------
if [[ -f "$FORK_DIR/setup-ipmi-limits.sh" ]]; then
    echo "==> Applying low-RPM sensor threshold fix"
    bash "$FORK_DIR/setup-ipmi-limits.sh" || echo "  (warn) threshold fix failed"
fi

# --- 6. Enable/start ----------------------------------------------------------
echo "==> Enabling $SERVICE"
systemctl enable "$SERVICE"
if [[ $START -eq 1 ]]; then
    echo "==> Starting $SERVICE"
    systemctl restart "$SERVICE"
    sleep 2
    systemctl --no-pager status "$SERVICE" || true
    echo ""
    echo "Monitor:  journalctl -u $SERVICE -f"
    echo "Return to BMC auto (optimal) if needed:"
    echo "  ipmitool raw 0x30 0x45 0x01 0x02"
else
    echo "Not started (--no-start). Start later with: systemctl start $SERVICE"
fi