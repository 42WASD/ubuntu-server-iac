#!/usr/bin/env bash
set -e

# ============================================================
#  vpn-persist.sh — Persistent GlobalProtect VPN via tmux
# ============================================================
#  Hybrid approach: manual SSO login (via connect-vpn.sh) PLUS
#  auto-reconnect if the tunnel drops.
#
#  Usage:
#    ./vpn-persist.sh start    # start VPN in a detached tmux session
#    ./vpn-persist.sh attach   # attach to the VPN session (view logs)
#    ./vpn-persist.sh stop     # stop the VPN session + kill openconnect
#    ./vpn-persist.sh status   # show tmux session status
# ============================================================

SESSION="vpn"
RESTART_DELAY=10

case "${1:-}" in
  start)
    # Kill any existing session first to avoid duplicates
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    echo "[+] Starting persistent VPN in tmux session '$SESSION'..."
    tmux new-session -d -s "$SESSION" \
      "while true; do cd ~ && ./connect-vpn.sh; echo '[!] VPN exited, restarting in ${RESTART_DELAY}s...'; sleep ${RESTART_DELAY}; done"
    echo "[+] Session started. Attach with: tmux attach -t $SESSION"
    ;;
  attach)
    tmux attach -t "$SESSION"
    ;;
  stop)
    echo "[-] Stopping VPN session and openconnect..."
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    sudo killall openconnect 2>/dev/null || true
    echo "[+] Stopped."
    ;;
  status)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "[+] VPN session '$SESSION' is RUNNING."
      tmux list-sessions
    else
      echo "[-] VPN session '$SESSION' is NOT running."
    fi
    ;;
  *)
    echo "Usage: $0 {start|attach|stop|status}"
    exit 1
    ;;
esac