#!/usr/bin/env bash
# gpauth-broadcast.sh
#
# Wrapper for `gpauth --browser remote` that makes the browser-auth URL
# reachable over Tailscale (and any host interface), instead of only the
# single LAN IP that gpauth hard-binds to.
#
# Why: gpauth (yuezk/GlobalProtect-openconnect) detects its "local IP" by
# UDP-connecting to 1.1.1.1 and binds the remote-browser auth server ONLY to
# that IP (see browser_auth.rs determine_addr()). On a box with Tailscale that
# detected IP is the LAN address, so the printed URL is unreachable from the
# Tailscale interface (100.x/10). There is no gpauth flag to override this.
#
# We solve it by watching the URL gpauth prints, then starting a `socat`
# forwarder that listens on 0.0.0.0:<port> and forwards to gpauth's
# LAN-bound <ip>:<port>. Both the LAN and Tailscale IP then work.

set -euo pipefail

GPAUTH="$(command -v gpauth)"

# If Tailscale isn't present, fall back to stock gpauth.
TS_IP="$(tailscale ip -4 2>/dev/null | head -n1 || true)"
if [ -z "$TS_IP" ]; then
  echo "[!] No Tailscale IP detected; running gpauth unchanged." >&2
  exec "$GPAUTH" "$@"
fi

LOG_FILE="$(mktemp)"         # gpauth's stderr is teed here so we can parse the URL
SOCAT_PID_FILE="$(mktemp)"   # lets cleanup kill the forwarder
SOCAT_PID=""
HELPER_PID=""

cleanup() {
  if [ -n "$SOCAT_PID" ]; then
    kill "$SOCAT_PID" 2>/dev/null || true
  elif [ -s "$SOCAT_PID_FILE" ]; then
    kill "$(cat "$SOCAT_PID_FILE")" 2>/dev/null || true
  fi
  [ -n "$HELPER_PID" ] && kill "$HELPER_PID" 2>/dev/null || true
  rm -f "$LOG_FILE" "$SOCAT_PID_FILE"
}
trap cleanup EXIT

# Background helper: poll gpauth's stderr for the auth URL, start a socat
# forwarder from 0.0.0.0 to the LAN-bound server, and print a reachable URL.
(
  for _ in $(seq 1 1000); do
    URL="$(grep -oE 'http://[0-9.]+:[0-9]+/[0-9a-f-]+' "$LOG_FILE" 2>/dev/null | head -n1 || true)"
    if [ -n "$URL" ]; then
      PORT="$(printf '%s' "$URL" | sed -E 's#http://[0-9.]+:([0-9]+)/.*#\1#')"
      LAN_IP="$(printf '%s' "$URL" | sed -E 's#http://([0-9.]+):.*#\1#')"
      AUTH_ID="$(printf '%s' "$URL" | sed -E 's#.*/([0-9a-f-]+)$#\1#')"
      socat "TCP-LISTEN:${PORT},bind=${TS_IP},reuseaddr,fork" "TCP:${LAN_IP}:${PORT}" &
      echo "$!" >"$SOCAT_PID_FILE"
      echo "" >&2
      echo "==== Auth URL (reachable via Tailscale / any interface) ====" >&2
      echo "" >&2
      echo "    http://${TS_IP}:${PORT}/${AUTH_ID}" >&2
      echo "" >&2
      # Keep the forwarder alive until the wrapper exits.
      wait 2>/dev/null || true
      exit 0
    fi
    sleep 0.1
  done
) &
HELPER_PID=$!

# Run gpauth in the foreground so its stdin stays on the terminal (the user
# pastes the auth callback there). Its stderr is teed so the helper can read
# the URL. Its stdout (the auth JSON) flows through to the caller unchanged.
"$GPAUTH" "$@" 2> >(tee "$LOG_FILE" >&2)