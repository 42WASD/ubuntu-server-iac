#!/usr/bin/env bash
# Phase 11 quota policy — source of truth.
# Owner (management): small box; developers: larger box. Units GiB.
set -euo pipefail
ROOT_FS="/"
OWNER_SOFT_GIB=6
OWNER_HARD_GIB=10
DEV_SOFT_GIB=10
DEV_HARD_GIB=15
gib_to_kb() { echo $(( $1 * 1024 * 1024 )); }
OWNER_SOFT_KB=$(gib_to_kb "$OWNER_SOFT_GIB")
OWNER_HARD_KB=$(gib_to_kb "$OWNER_HARD_GIB")
DEV_SOFT_KB=$(gib_to_kb "$DEV_SOFT_GIB")
DEV_HARD_KB=$(gib_to_kb "$DEV_HARD_GIB")
OWNER_USER="jyao"
DEV_USERS=(jyao-42admin ehammoud mayan mtangalv)
echo "== [1/4] usrquota in fstab =="
if ! grep -q "usrquota" /etc/fstab; then
  sudo sed -i '/^\/dev\/disk\/by-id\/dm-.*\/ ext4 defaults 0 1/s/defaults/defaults,usrquota/' /etc/fstab
fi
grep " / " /etc/fstab
echo "== [2/4] remount =="
sudo mount -o remount,usrquota / || true
echo "== [3/4] quotacheck + quotaon =="
sudo quotacheck -cum "$ROOT_FS" || true
sudo quotaon -v "$ROOT_FS" 2>&1 | grep -v tmpfs || true
echo "== [4/4] set quotas =="
sudo setquota -u "$OWNER_USER" "$OWNER_SOFT_KB" "$OWNER_HARD_KB" 0 0 "$ROOT_FS" 2>/dev/null || true
for u in "${DEV_USERS[@]}"; do
  sudo setquota -u "$u" "$DEV_SOFT_KB" "$DEV_HARD_KB" 0 0 "$ROOT_FS" 2>/dev/null || true
done
echo "== Done: repquota / =="
sudo repquota / 2>/dev/null | grep -v tmpfs | grep -E "User|^$OWNER_USER |$(IFS='|'; echo "${DEV_USERS[*]}")|-----" || true
