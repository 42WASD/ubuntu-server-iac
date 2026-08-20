#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  firewall-approval.sh — Phase 7 approval watcher (option 2)
# ============================================================
# LEARN-mode companion to host-filter.nft. The firewall accepts ALL traffic
# and logs new inbound connections (prefix "HOST-NEW"). This small tool:
#
#   * `watch`  tails journald for those HOST-NEW lines and prints them, so the
#              admin sees what is being used and we never accidentally block it,
#   * `allow`      <port> adds a permanent rule to the approved set,
#   * `allow-once` <port> inserts a temporary rule (a systemd timer cleans it up).
#
# Deliberately simple: tail logs + grep, plus two one-line commands. No state
# machine, no complex parsing — minimal chance of bugs.
# ============================================================

APPROVED_FILE="${FIREWALL_APPROVED_FILE:-/etc/nftables.d/approved-ports.nft}"
RULES_FILE="${FIREWALL_RULES_FILE:-/etc/nftables.d/host-filter.nft}"

usage() {
    cat <<'EOF'
Usage: firewall-approval.sh <command> [args]

  watch                 Follow HOST-NEW logs and print inbound connections.
  allow <port> [proto]  Permanently allow inbound <port> (default tcp).
  allow-once <port>     Temporarily allow a port (expires via systemd timer).
EOF
}

# Add a port permanently: append to the approved list, then reload only our
# table (deletes inet host_filter, reapplies from file — never a full flush).
allow_permanent() {
    local port="$1" proto="${2:-tcp}"
    if [ -e "$APPROVED_FILE" ] && grep -q "dport $port" "$APPROVED_FILE"; then
        echo "[+] $proto port $port already allowed."
        return 0
    fi
    echo "$proto dport $port accept" | sudo tee -a "$APPROVED_FILE" >/dev/null
    echo "[+] Added permanent rule: $proto dport $port"
    sudo nft -f "$RULES_FILE"
}

# One-time: insert an accept rule above the log rule. A systemd timer
# (platform-allow-timeout.timer) removes it after a set window.
allow_once() {
    local port="$1" proto="${2:-tcp}"
    echo "[+] Inserting temporary allow: $proto dport $port (auto-cleaned by timer)"
    sudo nft insert rule inet host_filter input "$proto dport $port accept"
}

watch() {
    echo "[+] Watching for new inbound connections (HOST-NEW) ..."
    echo "[+] Press Ctrl-C to stop."
    journalctl -f -o cat -t kernel --since "now" 2>/dev/null | grep --line-buffered "HOST-NEW" || true
}

case "${1:-}" in
    watch)        watch ;;
    allow)        [ $# -ge 2 ] && allow_permanent "$2" "${3:-tcp}" || usage ;;
    allow-once)   [ $# -ge 2 ] && allow_once "$2" "${3:-tcp}" || usage ;;
    *)            usage ;;
esac