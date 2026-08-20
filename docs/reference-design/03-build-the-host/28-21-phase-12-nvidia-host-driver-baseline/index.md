# Phase 12 — NVIDIA host driver baseline

Do this **before** Kubernetes GPU integration.

List recommended server/compute drivers:

```bash
sudo ubuntu-drivers list --gpgpu
```

Let Ubuntu choose the recommended compute driver:

```bash
sudo ubuntu-drivers install --gpgpu
```

Reboot:

```bash
sudo reboot
```

Verify:

```bash
nvidia-smi
```

Expected:

```text
both RTX 3090 GPUs visible
driver loaded
no NVML mismatch
```

Also inspect:

```bash
cat /proc/driver/nvidia/version
lspci -nn | grep -i nvidia
dmesg | grep -i -E 'nvrm|nvidia' | tail -100
```

## Do not install random `.run` driver packages from NVIDIA's website

For this host, prefer Ubuntu-packaged drivers unless you have a specific compatibility reason.

## Checkpoint 9

Reboot twice.

After each reboot:

```bash
nvidia-smi
systemctl --failed
```

If GPU driver reliability is not proven, do not continue into GPU Operator/HAMi later.

The base Kubernetes platform can still continue.

---
