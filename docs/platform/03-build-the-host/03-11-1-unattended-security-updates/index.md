# unattended security updates

Inspect:

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null || true
cat /etc/apt/apt.conf.d/50unattended-upgrades
```

Enable through Ubuntu's normal mechanism:

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

Recommended policy:

```text
automatic security updates: yes

automatic reboot:
  not blindly during work hours
```

For kernel/NVIDIA/RKE2 hosts, prefer:

```text
security package installs automatically
reboot is explicit/maintenance-window controlled
```

because a driver/kernel mismatch may require a reboot.

## Checkpoint 2

```bash
systemctl --failed
timedatectl
sudo aa-status
```

Expected:

```text
no unexplained failed units
clock synchronized
AppArmor loaded
```

---
