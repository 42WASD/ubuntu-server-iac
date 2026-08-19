# Host `beta` — NVIDIA Driver & GPU Power Limiting

This guide covers the NVIDIA driver setup and GPU power limiting on the
secondary server **`beta`** (`192.168.8.135`).

## Hardware

| GPU | Bus | Architecture | Status |
|-----|-----|--------------|--------|
| NVIDIA GeForce GTX 1070 | `0000:07:00.0` | Pascal (GP104) | **Working** |
| NVIDIA GeForce RTX 3070 Mobile / Max-Q | `0000:06:00.0` | Ampere (GA104M) | ❌ fails to init |

## Driver Selection: 580 (not 595)

The first attempt installed the **595** server driver
(`nvidia-headless-595-server`, 595.71.05). The 595 branch **dropped Pascal
support**, so the GTX 1070 was ignored at boot:

```
NVRM: ignoring the legacy GPU 0000:07:00.0
```

The RTX 3070 Mobile also failed under 595 with `RmInitAdapter failed (0x62:0x55:2830)`.

The **580** server driver (`nvidia-headless-580-server`, 580.173.02) supports
both Pascal and Ampere, and is the correct branch for this mixed dual-GPU host.

## Install (what was done)

```bash
# 1. Switch from 595 to 580
sudo apt-get install -y nvidia-headless-580-server
sudo apt-get purge -y nvidia-headless-595-server nvidia-utils-595-server \
    libnvidia-compute-595-server nvidia-kernel-common-595-server

# 2. Install the SMI utilities (purged alongside 595)
sudo apt-get install -y nvidia-utils-580-server

# 3. Reload the kernel module (or reboot)
sudo modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia
sudo modprobe nvidia
```

## Result

`nvidia-smi` now reports the **GTX 1070**:

```text
NVIDIA-SMI 580.173.02   Driver Version: 580.173.02   CUDA Version: 13.0
0  NVIDIA GeForce GTX 1070   P0   32W / 75W   0MiB / 8192MiB
```

## Power Limit (GTX 1070 → 75W)

Per the owner's instruction, the GTX 1070 is capped at the **lowest supported
power limit of 75W** (the supported range is 75–170W).

Set and verify manually:

```bash
sudo nvidia-smi -i 0 -pl 75
nvidia-smi -q -i 0 -d POWER | grep -iE 'Current Power Limit'   # -> 75.00 W
```

Persistence mode is enabled so the limit stays applied:

```bash
sudo nvidia-smi -pm 1
```

### Persist at boot (systemd)

A unit is committed at `scripts/gpu/beta-nvidia-power-limit.service`.

```bash
sudo cp scripts/gpu/beta-nvidia-power-limit.service /etc/systemd/system/nvidia-power-limit.service
sudo systemctl daemon-reload
sudo systemctl enable --now nvidia-power-limit.service
```

Verify:

```bash
systemctl status nvidia-power-limit.service
nvidia-smi --query-gpu=index,name,power.limit,persistence_mode --format=csv
```

## RTX 3070 Mobile — still failing

The `GA104M` (RTX 3070 Mobile / Max-Q) fails to initialize under both 595 and
580. The failure mode changes depending on the GSP-firmware setting:

- **GSP firmware enabled (default)** — `RmInitAdapter failed (0x62:0x55:2674)`
- **GSP firmware disabled** (`NVreg_EnableGpuFirmware=0`) — the error moves
  earlier to `RmInitAdapter failed (0x31:0x40:2780)`, but the card still never
  initializes.

The GSP-off setting was tried and persisted in `/etc/modprobe.d/nvidia-gsp-off.conf`
(`options nvidia NVreg_EnableGpuFirmware=0`), but it did **not** make the card work.

### Root cause: missing/invalid vBIOS (likely hardware)

Strong evidence points to a vBIOS problem on this "frankenstein" mobile chip
(mobile GPU bolted onto a desktop adapter):

- `/proc/driver/nvidia/gpus/0000:06:00.0/information` reports
  `Video BIOS: ??.??.??.??.??` — the driver **cannot read the vBIOS**.
- The card's subsystem ID is blank/zero (`NVIDIA Corporation Device 0000`),
  a hallmark of a missing or mismatched vBIOS.
- The GSP firmware error changes but never resolves, consistent with a card that
  cannot initialize at the firmware level.

Because the card never comes up, it **cannot be queried or power-limited**.

### Possible next steps (hardware/firmware level)

1. **vBIOS** — flash a matching mobile RTX 3070 vBIOS onto the adapter. This is
   the most likely fix, but it is risky and requires the card to be flashed
   (typically via a Windows tool or `nvflash`).
2. **BIOS settings** — confirm `Above 4G Decoding` and **Resizable BAR** are
   consistent in the BIOS for the slot.
3. **Power delivery** — verify the auxiliary 6/8-pin is seated; mobile chips need
   a specific power sequence a desktop adapter may not provide.
4. **Seat / reseat** — reinsert the card and confirm the slot link is stable.

Until this is resolved, **only the GTX 1070** is available on `beta`, capped at 75W.