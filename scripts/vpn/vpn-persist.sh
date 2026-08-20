#!/usr/bin/env bash
set -e

# ============================================================
#  vpn-persist.sh — Persistent GlobalProtect VPN via tmux
# ============================================================
SESSION="vpn"
RESTART_DELAY=10

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONNECT_SCRIPT="$SCRIPT_DIR/connect-vpn.sh"

case "${1:-}" in
  start)
    # Verify the connect script exists before starting
    if [ ! -x "$CONNECT_SCRIPT" ]; then
        echo "[-] Error: $CONNECT_SCRIPT not found or not executable."
        exit 1
    fi

    # Kill any existing session first to avoid duplicates
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    
    echo "[+] Starting persistent VPN in tmux session '$SESSION'..."
    tmux new-session -d -s "$SESSION" \
      "while true; do $CONNECT_SCRIPT; echo '[!] VPN exited, restarting in ${RESTART_DELAY}s...'; sleep ${RESTART_DELAY}; done"
    
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

  connect|single)
    # Run ONE connection in the foreground in the CURRENT terminal.
    # This does NOT touch or restart the persistent tmux '$SESSION'.
    # Useful for testing (e.g. the Tailscale auth URL) alongside the
    # persistent session. Exit when the tunnel drops.
    echo "[+] Running a single VPN connection (foreground, tmux '$SESSION' untouched)..."
    if [ ! -x "$CONNECT_SCRIPT" ]; then
        echo "[-] Error: $CONNECT_SCRIPT not found or not executable."
        exit 1
    fi
    exec "$CONNECT_SCRIPT"
    ;;
    
  *)
    echo "Usage: $0 {start|attach|stop|status|connect}"
    echo "  start      Run persistent VPN loop in tmux session '$SESSION'"
    echo "  attach     Attach to the tmux session"
    echo "  stop       Stop the tmux session and openconnect"
    echo "  status     Show whether the tmux session is running"
    echo "  connect    Run a single VPN connection in this terminal (no tmux)"
    exit 1
    ;;
esac