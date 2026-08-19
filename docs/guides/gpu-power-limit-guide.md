# GPU Power Limiting

This guide documents how the **2 × NVIDIA RTX 3090** GPUs on the server (`alpha`) are power-limited to **300W** each and kept persistent across reboots using a **systemd service**.

## Why Limit GPU Power?

The RTX 3090 ships with a **350W** default power limit. In this particular system, GPU 0 was found running at **390W** (above stock — likely from a prior overclock/undervolt tool). Capping both cards at **300W** delivers:

- **Near-stock performance** (roughly 5–8% loss in the worst case, often less)
- **Significantly lower power draw and heat** — important for a shared/limited PSU
- **More stable multi-GPU operation** (fewer thermal/power-trip dropouts)
- Lower noise and cooler VRM temperatures

## Current Power Limit Ranges

Verified via `nvidia-smi` (before applying limits):

| GPU | Current Limit | Min | Max |
|-----|--------------|-----|-----|
| 0 | 390 W (was 350 stock) | 100 W | 480 W |
| 1 | 350 W (stock) | 100 W | 365 W |

Both cards support a **300W** target.

## Service File

The service definition is committed to the repo at:

```
scripts/gpu/gpu-power-limit.service
```

```ini title="scripts/gpu/gpu-power-limit.service"
[Unit]
Description=Set NVIDIA GPU power limits to 300W and enable persistence mode
After=multi-user.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
RemainAfterExit=yes
# Persistence mode keeps the driver loaded so power limits stay applied.
ExecStart=/usr/bin/nvidia-smi -pm 1
# Apply a 300W power limit to both RTX 3090 GPUs.
ExecStart=/usr/bin/nvidia-smi -i 0 -pl 300
ExecStart=/usr/bin/nvidia-smi -i 1 -pl 300

[Install]
WantedBy=multi-user.target
```

## Why a systemd Service?

Power limits and persistence mode **reset whenever the driver reloads** (on reboot or driver swap). Running them as a `systemd` service with `Type=oneshot` + `WantedBy=multi-user.target` ensures they are **re-applied automatically at every boot**.

## Install & Enable

```bash
# 1. Copy the service into the systemd directory
sudo cp scripts/gpu/gpu-power-limit.service /etc/systemd/system/

# 2. Reload systemd so it picks up the new unit
sudo systemctl daemon-reload

# 3. Enable (start at boot) and start it now
sudo systemctl enable --now gpu-power-limit.service
```

## Verification

Check that both GPUs report a **300W** limit and **Enabled** persistence mode:

```bash
nvidia-smi --query-gpu=index,name,power.limit,persistence_mode --format=csv
```

Expected output:

```text
index, name, power.limit [W], persistence_mode
0, NVIDIA GeForce RTX 3090, 300.00 W, Enabled
1, NVIDIA GeForce RTX 3090, 300.00 W, Enabled
```

Confirm the service is active and enabled:

```bash
systemctl status gpu-power-limit.service
systemctl is-enabled gpu-power-limit.service   # -> enabled
```

## Adjusting the Limit

To change the target wattage, edit the `ExecStart` lines in the service file, then reload:

```bash
sudo nano /etc/systemd/system/gpu-power-limit.service   # e.g. change 300 to 280
sudo systemctl daemon-reload
sudo systemctl restart gpu-power-limit.service
```

For reference, common RTX 3090 targets:

| Limit | Effect |
|-------|--------|
| 350 W | Stock |
| 300 W | Conservative cap (current) — near-stock perf, big savings |
| 280 W | Common "safe" target ~5–8% perf loss |
| 250 W | Aggressive — larger perf hit, maximum savings |

!!! note
    Apply limits within each GPU's supported range. GPU 0 supports 100–480 W; GPU 1 supports 100–365 W. `nvidia-smi` will reject values outside that card's range.