# journald bound

Create:

```bash
sudoedit /etc/systemd/journald.conf.d/50-platform.conf
```

Example:

```ini
[Journal]
SystemMaxUse=4G
SystemKeepFree=8G
RuntimeMaxUse=1G
MaxRetentionSec=14day
Compress=yes
```

Restart:

```bash
sudo systemctl restart systemd-journald
```

Check:

```bash
journalctl --disk-usage
```

---
