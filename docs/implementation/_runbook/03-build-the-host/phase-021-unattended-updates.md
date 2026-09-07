---
phase: 03-build-the-host/update-ubuntu-and-install-base-administration-tools/unattended-security-updates
---

# Phase 2.1 — unattended security updates

**Intent:** confirm automatic security updates are on, reboots controlled.

Covered by the `base` role (template deployed in Phase 2). Policy:
security-updates auto, **reboots never automatic** — the reboot is an
explicit maintenance action driven by `/var/run/reboot-required`.

**2026-09-07 policy change — `Automatic-Reboot "false"`.** The host had
`Automatic-Reboot "true"` + time 03:00; unattended-upgrades installed a
kernel on 09-06 and auto-rebooted the node at 03:00 on 09-07, which killed
`fancontrol` (hwmon drift) and bounced every workload unannounced. Why the
auto-reboot default is bad on a single-node platform:

- no HA: an unchosen reboot = full-cluster outage (RKE2, storage, games);
- `Automatic-Reboot-Time` makes the surprise predictable in when, not
  whether — it can still hit a backup or long job;
- boot-order fragility: hwmon indices swap between boots; services can come
  up broken with nobody watching (exactly what happened);
- patch install (low risk) and kernel restart (highest-risk routine op)
  should not share one boolean.

```bash
# Applied on alpha 2026-09-07:
sudo sed -i 's/^Unattended-Upgrade::Automatic-Reboot "true";/Unattended-Upgrade::Automatic-Reboot "false";/' \
  /etc/apt/apt.conf.d/50unattended-upgrades
apt-config dump | grep 'Automatic-Reboot '   # -> "false"
```

The `base` role template now ships `Automatic-Reboot "false"` by default.
New rule of record: when `/var/run/reboot-required` appears, reboot
explicitly in a maintenance window, then run `systemctl --failed`.

**Checkpoint (verified):** `systemctl --failed`, `timedatectl`, `aa-status` all
clean.