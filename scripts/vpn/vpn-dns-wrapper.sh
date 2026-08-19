#!/bin/bash

# 1. Run the original vpnc-script to handle routes and the TUN interface
/usr/share/vpnc-scripts/vpnc-script

# 2. Manually fix DNS for systemd-resolved on connect or reconnect
if [ "$reason" = "connect" ] || [ "$reason" = "reconnect" ]; then
    if command -v resolvectl >/dev/null 2>&1; then
        IFACE="$TUNDEV"
        echo "[+] Applying VPN DNS settings to systemd-resolved..."
        
        # Clear any stale settings for this interface
        resolvectl revert "$IFACE" >/dev/null 2>&1
        
        # Set the Internal DNS servers pushed by the VPN
        if [ -n "$INTERNAL_IP4_DNS" ]; then
            resolvectl dns "$IFACE" $INTERNAL_IP4_DNS
        fi
        
        # Collect all domains pushed by the VPN (CISCO_DEF_DOMAIN, CISCO_SPLIT_DNS, etc.)
        DOMAINS=""
        [ -n "$CISCO_DEF_DOMAIN" ] && DOMAINS="$CISCO_DEF_DOMAIN"
        [ -n "$CISCO_SPLIT_DNS" ] && DOMAINS="$DOMAINS $(echo "$CISCO_SPLIT_DNS" | tr ',' ' ')"
        
        # GlobalProtect sometimes passes domains via SPLIT_INC
        if [ -n "$CISCO_SPLIT_INC" ]; then
            i=0
            while [ $i -lt "$CISCO_SPLIT_INC" ]; do
                eval DOMAIN="\${CISCO_SPLIT_INC_${i}_DOMAIN}"
                [ -n "$DOMAIN" ] && DOMAINS="$DOMAINS $DOMAIN"
                i=$((i + 1))
            done
        fi
        
        # Apply domains as both "search domains" and "routing domains" (~)
        if [ -n "$DOMAINS" ]; then
            DOMAIN_ARGS=""
            for d in $DOMAINS; do
                # The ~ prefix marks it as a routing domain (Split DNS)
                DOMAIN_ARGS="$DOMAIN_ARGS $d ~$d"
            done
            resolvectl domain "$IFACE" $DOMAIN_ARGS
        fi
    fi
fi

# 3. Cleanup DNS on disconnect
if [ "$reason" = "disconnect" ]; then
    if command -v resolvectl >/dev/null 2>&1; then
        IFACE="$TUNDEV"
        echo "[-] Clearing VPN DNS settings from systemd-resolved..."
        resolvectl revert "$IFACE" >/dev/null 2>&1
    fi
fi
