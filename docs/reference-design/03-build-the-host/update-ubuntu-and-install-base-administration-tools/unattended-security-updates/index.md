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

automatic reboot: NO
```

**Why automatic reboots are disabled (policy, not preference):**

- **Single node = no HA.** A reboot nobody chose is a full-platform outage:
  RKE2, pods, persistent storage, and every hosted service go down at a time
  nobody scheduled work around. On a multi-node cluster a rolling reboot is
  routine; here it is an incident.
- **Reboot time ≠ maintenance window.** `Automatic-Reboot-Time "03:00"` only
  makes the surprise predictable in *when*, not in *whether* — it can hit
  during a backup, a long-running job, or days of uptime you relied on.
- **Boot-order fragility is real.** Kernel updates change hardware module
  load order; services can come up broken after an unattended reboot
  (2026-09-07: fancontrol died after an auto-reboot because hwmon indices
  swapped and its boot-time generator wasn't enabled).
- **Updates and reboots have different risk profiles.** Installing security
  patches automatically is low-risk and reversible; restarting the kernel is
  the single riskiest routine operation on the host. They should not be
  gated by the same boolean.
- **No warning surface.** Auto-reboot gives at most a logind console
  countdown at 03:00 — nobody is watching. A manual reboot starts from
  `/var/run/reboot-required`, is announced, and happens when you can watch
  services come back.

Operating procedure:

```bash
# Notice the flag (check after login / in monitoring):
cat /var/run/reboot-required 2>/dev/null && echo "reboot needed"
# Reboot explicitly in a maintenance window, then verify:
sudo reboot
systemctl --failed   # after boot
```

The kernel/NVIDIA/RKE2 rule stays as-is — security package installs are
automatic, reboots are explicit and maintenance-window controlled.

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
