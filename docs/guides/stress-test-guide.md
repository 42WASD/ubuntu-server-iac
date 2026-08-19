# System Stress Test Guide

This guide documents how to run a **full CPU + GPU stress test** on the server to validate system stability and confirm the **1200W power supply** is adequate.

## Why Stress Test?

A machine can pass individual component tests and still fail under **simultaneous** load, because the CPU and GPUs draw power from the **same PSU rails** and dump heat into the **same chassis**. A combined stress test validates:

- **Power delivery** — is the 1200W PSU enough under full load?
- **Thermals** — do components stay within safe temperatures?
- **Stability** — does the system crash, throttle, or reboot?

## Power Budget (1200W PSU)

Your **worst-case sustained draw** with 300W GPU caps:

| Component | Max Draw |
|-----------|----------|
| GPU 0 (RTX 3090) | 300 W |
| GPU 1 (RTX 3090) | 300 W |
| CPU (EPYC 7742) | ~225 W |
| RAM (107 GB) | ~40 W |
| Motherboard / NVMe / fans | ~60 W |
| **Total worst-case** | **~925 W** |

With ~925W under full load, the 1200W PSU has a healthy **~275W (23%) headroom**. This is comfortable. The 300W GPU caps (applied by the systemd `gpu-power-limit` service) are important here — without them, GPU 0 could spike to its 480W max.

## Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `stress-ng` | CPU/FPU/memory stress | `sudo apt install stress-ng` |
| `gpu-burn` | NVIDIA GPU stress | Build from [wilicc/gpu-burn](https://github.com/wilicc/gpu-burn) (needs CUDA toolkit) |
| `nvtop` | GPU live monitoring | `sudo apt install nvtop` |
| `htop` | CPU live monitoring | `sudo apt install htop` |

`gpu-burn` requires the CUDA toolkit to build (it links `cublas` + `cudart`):

```bash
cd /tmp
git clone https://github.com/wilicc/gpu-burn.git
cd gpu-burn
make
sudo cp gpu_burn /usr/local/bin/
```

## Scripts

The repo contains two helper scripts under `scripts/stress/`:

### 1. `stress-test.sh` — Main launcher

Runs the full simultaneous test:

```bash
sudo ./scripts/stress/stress-test.sh 300    # 5 minute full burn
```

What it does:
1. Launches `stress-ng` on **all 128 threads** (`matrixprod,fft` methods)
2. Launches `gpu_burn` on **both RTX 3090s**
3. Runs the monitor alongside to capture power/thermal data
4. Cleans up and prints the log path

### 2. `monitor-stress.sh` — Power/thermal logger

Samples CPU RAPL power, both GPUs' power/utilization, and CPU temps every second into a timestamped CSV:

```bash
./scripts/stress/monitor-stress.sh 300 2
```

Columns logged: `timestamp, cpu_package_w, gpu0_w, gpu1_w, gpu0_util, gpu1_util, gpu0_mem, gpu1_mem, tctl_c, ccd1_c, ccd2_c`

## Recommended Test Procedure

For a **thorough** validation, run in this order:

1. **Idle baseline** — record idle power/temps:
   ```bash
   ./scripts/stress/monitor-stress.sh 60
   ```

2. **CPU-only stress** (5 min):
   ```bash
   stress-ng --cpu $(nproc) --cpu-method matrixprod,fft --timeout 300s
   ```

3. **GPU-only stress** (5 min):
   ```bash
   /usr/local/bin/gpu_burn 300
   ```

4. **Full simultaneous stress** (10 min) — the critical test:
   ```bash
   sudo ./scripts/stress/stress-test.sh 600
   ```

## Interpreting Results

| Metric | Safe Range | Concern |
|--------|-----------|---------|
| CPU temp (`Tctl`) | < 85°C | > 90°C sustained |
| GPU temp | < 83°C | > 90°C |
| Total power | < ~1000W | near 1200W PSU limit |
| Stability | no crashes/reboots | systemd/driver errors |

## Power Limit Interaction

The GPU power caps (300W, applied at boot by `gpu-power-limit.service`) are active during the test. To test **without** caps (worst case), raise or remove the limit first:

```bash
sudo nvidia-smi -i 0 -pl 350
sudo nvidia-smi -i 1 -pl 350
```

Then run the stress test. **Note:** running uncapped raises total draw to ~1025W, still within the 1200W PSU but with less margin.

!!! warning
    Stress testing pushes hardware to its limits. Ensure adequate cooling before running. Monitor the first 30 seconds closely. Ctrl+C to abort.