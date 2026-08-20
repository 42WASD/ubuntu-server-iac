# Phase 9 — developer CPU/RAM/PID limits on the host

Remote builds will protect alpha from Docker build spikes.

Developers can still run:

```text
pytest -n 64
make -j64
a runaway Python program
10000 child processes
```

So host users still need cgroup limits.

Systemd creates a user slice for each UID.

Find UID:

```bash
id -u jya0
id -u alice
```

For example, if Alice is UID `1005`:

```bash
sudo mkdir -p /etc/systemd/system/user-1005.slice.d
sudoedit /etc/systemd/system/user-1005.slice.d/50-platform-limits.conf
```

Example normal-developer policy:

```ini
[Slice]
CPUQuota=400%
MemoryHigh=8G
MemoryMax=12G
TasksMax=4096
IOWeight=50
```

Interpretation:

```text
CPUQuota=400%
    approximately four CPU cores worth of scheduler time

MemoryHigh=8G
    pressure/throttling boundary

MemoryMax=12G
    hard cgroup ceiling

TasksMax=4096
    process/thread ceiling

IOWeight=50
    lower I/O priority than default-weight services
```

For `jya0`, a larger profile may be appropriate:

```ini
[Slice]
CPUQuota=800%
MemoryHigh=16G
MemoryMax=24G
TasksMax=8192
IOWeight=75
```

Reload:

```bash
sudo systemctl daemon-reload
```

Existing user sessions may need to log out completely before a new slice instance picks up changes.

Check:

```bash
systemctl status user-$(id -u alice).slice
systemctl show user-$(id -u alice).slice \
  -p CPUQuotaPerSecUSec \
  -p MemoryHigh \
  -p MemoryMax \
  -p TasksMax \
  -p IOWeight
```

## Important distinction

These limits protect the **host**.

Kubernetes ResourceQuota protects a **namespace**.

BuildKit limits protect the **builder**.

Use all three at the appropriate layer.

---
