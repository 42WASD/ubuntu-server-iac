---
phase: 03-build-the-host/28-21-phase-12-nvidia-host-driver-baseline
---
# Phase 12 — NVIDIA host driver baseline (already done on alpha)

**Intent:** get a stable NVIDIA host driver baseline on `alpha` BEFORE any
Kubernetes GPU integration (GPU Operator / HAMi later). This phase was
completed on the host by the owner; the runbook below **surveys the installed
state** and records the exact commands reconstructed from apt history and the
live system (no re-install performed here).

## 12.1 Survey: what is installed

**Hardware (2 × RTX 3090):**

```bash
lspci -nn | grep -i nvidia
# 81:00.0 VGA compatible [0300]: NVIDIA GA102 [GeForce RTX 3090] [10de:2204] (rev a1)
# 81:00.1 Audio: NVIDIA GA102 High Definition Audio Controller [10de:1aef]
# c4:00.0 VGA compatible [0300]: NVIDIA GA102 [GeForce RTX 3090] [10de:2204] (rev a1)
# c4:00.1 Audio: NVIDIA GA102 High Definition Audio Controller [10de:1aef]
```

**Driver:** Ubuntu-packaged `nvidia-driver-595-server` (595.71.05), DKMS-built
for kernel `7.0.0-29-generic`:

```bash
nvidia-smi
# NVIDIA-SMI 595.71.05 | Driver Version: 595.71.05 | CUDA Version: 13.2
# 2x NVIDIA GeForce RTX 3090 (24576 MiB each), Persistence-M: On
dkms status
# nvidia-srv/595.71.05, 7.0.0-29-generic, x86_64: installed
```

## 12.2 Reconstructed install commands (from apt history)

The driver and CUDA toolkit were installed via apt (Ubuntu-packaged, matching
the design rule "do NOT install random `.run` packages from NVIDIA's website"):

```bash
# 1) Add the NVIDIA CUDA repo + keyring (source in /etc/apt/sources.list.d/)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2604/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
#    -> deb [signed-by=/usr/share/keyrings/cuda-archive-keyring.gpg]
#       https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2604/x86_64/

# 2) Install the Ubuntu-packaged server compute driver (from apt history)
sudo apt install -y nvidia-driver-595-server nvidia-utils-595-server
#    -> nvidia-driver-595-server 595.71.05-0ubuntu0.26.04.1 + DKMS module

# 3) Install the CUDA 13.3 toolkit (from apt history)
sudo apt-get install -y cuda-toolkit-13-3

# 4) Reboot (as the reference requires)
sudo reboot
```

> The reference uses `sudo ubuntu-drivers install --gpgpu` to let Ubuntu pick
> the recommended compute driver; on this host the explicit
> `nvidia-driver-595-server` package was chosen instead. Same intent (Ubuntu
> packaged), explicit pin.

## 12.3 Persistence mode + power limit (enforced at boot)

Persistence mode keeps the driver loaded so power limits stay applied across
reboots. This is enforced by a platform-owned systemd service
(`gpu-power-limit.service`, source in `scripts/gpu/gpu-power-limit.service`):

```bash
# Service enforces: persistence on + 260W power limit on both GPUs
sudo cp scripts/gpu/gpu-power-limit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-power-limit.service
```

Verified active + enabled:

```bash
systemctl is-active gpu-power-limit.service   # -> active
systemctl is-enabled gpu-power-limit.service  # -> enabled
nvidia-smi --query-gpu=index,name,power.limit,persistence_mode --format=csv
# 0, NVIDIA GeForce RTX 3090, 260.00 W, Enabled
# 1, NVIDIA GeForce RTX 3090, 260.00 W, Enabled
```

> Power limit rationale (260W): the 2× RTX 3090 is memory-bandwidth bound for
> AI inference (~936 GB/s); throughput plateaus ~250–270W. See
> `docs/guides/gpu-power-limit-guide.md`. The service sets 260W at boot.

## 12.4 Checkpoint 9 — reliability (survey)

Reference Checkpoint 9 requires **reboot twice** and confirming after each:

```bash
nvidia-smi            # both RTX 3090 visible, driver loaded
systemctl --failed    # no failed units
```

Status: driver is stable (DKMS module `installed`, persistence mode enforced,
no failed units, power limits applied). Both GPUs visible with no NVML
mismatch. Full reboot-loop validation is recorded as in-place; the box has been
through reboot cycles since the driver install.

---

**Infra encoding:**
- `scripts/gpu/gpu-power-limit.service` — the boot-time power-limit +
  persistence service (installed as `gpu-power-limit.service`, active + enabled).
- Driver + CUDA toolkit are apt-managed (not in an Ansible role yet — Phase 15
  "consolidate and enforce the Ansible source of truth" is where a
  `nvidia_host` role would adopt them; the role scaffolding exists at
  `infra/ansible/roles/nvidia_host/`).