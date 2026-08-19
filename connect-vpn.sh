#!/usr/bin/env bash
set -e

# === 1. Resolve paths in the current user context (before sudo is involved) ===
# Bash expands '~' correctly here, preventing the sudo environment bug.
DNS_WRAPPER=~/vpn-dns-wrapper.sh

# Setup HIP script location (GlobalProtect health check)
HIP_DIR=~/.config/openconnect
mkdir -p "$HIP_DIR"
HIP_SCRIPT=$(find /usr /etc /opt "$HIP_DIR" -name "hipreport.sh" 2>/dev/null | head -n 1)

if [ -z "$HIP_SCRIPT" ]; then
    echo "[!] hipreport.sh not found on system. Downloading official script..."
    curl -s -o "$HIP_DIR/hipreport.sh" https://gitlab.com/openconnect/openconnect/-/raw/master/trojans/hipreport.sh
    chmod +x "$HIP_DIR/hipreport.sh"
    HIP_SCRIPT="$HIP_DIR/hipreport.sh"
fi

# === 2. SAML Authentication ===
echo "=== 1. Starting SAML Authentication ==="
AUTH_JSON=$(gpauth --browser remote --gateway vpn.ecouncil.ae)

COOKIE=$(echo "$AUTH_JSON" | grep -o '"preloginCookie":"[^"]*' | cut -d'"' -f4)
USER=$(echo "$AUTH_JSON" | grep -o '"username":"[^"]*' | cut -d'"' -f4)

if [ -z "$COOKIE" ]; then
    echo "[-] Error: Failed to obtain prelogin cookie."
    exit 1
fi

# === 3. Establish VPN Tunnel ===
echo "=== 2. Establishing VPN Tunnel for $USER ==="
echo "[+] Using DNS wrapper: $DNS_WRAPPER"
echo "[+] Using HIP script: $HIP_SCRIPT"

echo "$COOKIE" | sudo openconnect --protocol=gp \
  -u "$USER" \
  --usergroup=gateway:prelogin-cookie \
  --os=win \
  --script="$DNS_WRAPPER" \
  --csd-wrapper="$HIP_SCRIPT" \
  --passwd-on-stdin \
  vpn.ecouncil.ae
