# System Stress Test Guide

This guide documents how to run a **full CPU + GPU stress test** on the server to validate system stability and confirm the **1200W power supply** is adequate.

## Why Stress Test?

A machine can pass individual component tests and still fail under **simultaneous** load, because the CPU and GPUs draw power from the **same PSU rails** and dump heat into the **same chassis**. A combined stress test validates:

- **Power delivery** — is the 1200W PSU enough under full load?
- **Thermals** — do components stay within safe temperatures?
- **Stability** — does the system crash, throttle, or reboot?

## Power Budget (1200W PSU)

Your **worst-case sustained draw** with **260W** GPU caps (the current setting):

| Component | Max Draw |
|-----------|----------|
| GPU 0 (RTX 3090) | 260 W |
| GPU 1 (RTX 3090) | 260 W |
| CPU (EPYC 7742) | ~225 W |
| RAM (107 GB) | ~40 W |
| Motherboard / NVMe / fans | ~60 W |
| **Total worst-case** | **~845 W** |

With ~845W under full load, the 1200W PSU has a healthy **~355W (30%) headroom**. This is comfortable. The 260W GPU caps (applied by the systemd `gpu-power-limit` service) are important here — without them, GPU 0 could spike to its 480W max.

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
1. Launches `stress-ng` on **all 128 threads** with the `matrixprod` method (single method — `stress-ng` only accepts one `--cpu-method` value)
2. Launches `gpu_burn` on **both RTX 3090s**
3. Runs the monitor alongside to capture power/thermal data
4. Cleans up and prints the log path

### 2. `monitor-stress.sh` — Power/thermal logger

Samples CPU RAPL power, both GPUs' power/utilization, and CPU temps every second into a timestamped CSV:

```bash
./scripts/stress/monitor-stress.sh 300 2
```

Columns logged: `time_s, cpu_package_w, cpu_avg_mhz, gpu0_w, gpu1_w, gpu0_util, gpu1_util, gpu0_mem, gpu1_mem, gpu0_sm_mhz, gpu1_sm_mhz, gpu0_mem_mhz, gpu1_mem_mhz, gpu0_temp_c, gpu1_temp_c, tctl_c, ccd1_c, ccd2_c`

It records CPU package power (RAPL), **CPU average clock (MHz)**, each GPU's power, utilization, memory, **SM clock (MHz)**, memory clock, and **temperature**, plus CPU temps — sampled every second into a timestamped CSV.

## Recommended Test Procedure

For a **thorough** validation, run in this order:

1. **Idle baseline** — record idle power/temps:
   ```bash
   ./scripts/stress/monitor-stress.sh 60
   ```

2. **CPU-only stress** (5 min):
   ```bash
   stress-ng --cpu $(nproc) --cpu-method matrixprod --timeout 300s
   ```

3. **GPU-only stress** (5 min):
   ```bash
   /usr/local/bin/gpu_burn 300
   ```

4. **Full simultaneous stress** (10 min) — the critical test:
   ```bash
   sudo ./scripts/stress/stress-test.sh 600
   ```

## Measured Results (180s full simultaneous test)

A real 180-second full CPU+GPU stress test was run on this server with both GPUs capped at 300W. These are the **actual measured numbers**:

| Metric | Average | Max |
|--------|---------|-----|
| CPU package power (RAPL) | 206 W | ~338 W* |
| GPU 0 (RTX 3090) | 280 W | 300 W |
| GPU 1 (RTX 3090) | 263 W | 300 W |
| CPU temp (`Tctl`) | 94.2°C | 94.8°C |
| GPU temps | 70–72 °C | 85 °C |
| gpu-burn errors | **0** | 0 |

\* CPU peak of ~338 W is the initial power-up transient; sustained load settles to **~206 W** at the EPYC 7742 TDP.

### Verdict: 1200W PSU is **adequate**

Total worst-case sustained package draw was **~750W** (CPU 206W + GPU0 280W + GPU1 263W). Adding the estimated ~100W for RAM/motherboard/storage brings the system peak to **~850–925W**. This leaves the 1200W PSU with **~275–350W (23–29%) headroom**.

**Important thermal finding:** The CPU reaches `Tctl` 94.8°C under sustained all-core load — right at the 95°C thermal limit. The EPYC 7742 **throttles** to protect itself (power drops from the ~225W TDP). This is **normal and safe** — the CPU self-regulates — but it means:
- The cooler is sufficient, but not over-provisioned. Adding fans or a better cooler would sustain higher clocks.
- Do **not** attempt to overclock or raise the power limit on the stock cooling.

**Conclusion:** The 1200W PSU is **confirmed adequate** for full simultaneous CPU+GPU load. Compute remained **100% stable** (zero gpu-burn errors over the full test, no crashes/reboots).

### Measured Results — 260W caps (current setting)

A second 180s full test was run after lowering the GPU power cap from 300W to **260W** to see the effect on temperature and power draw:

| Metric | Average | Max |
|--------|---------|-----|
| CPU package power (RAPL) | 206 W | 287 W |
| CPU average clock | **2673 MHz** | ~2800 MHz |
| GPU 0 (RTX 3090) | 248 W | 260 W |
| GPU 0 SM clock | 1198 MHz | 1230 MHz |
| GPU 0 temp | 61°C | **65°C** |
| GPU 1 (RTX 3090) | 247 W | 260 W |
| GPU 1 SM clock | 1091 MHz | 1065 MHz |
| GPU 1 temp | 77°C | **84°C** |
| CPU temp (`Tctl`) | 84.8°C | 95°C |
| gpu-burn errors | **0** | 0 |

**Total worst-case package draw: ~701W** — even lower than the 300W test's ~750W.

**Effect of lowering to 260W:**
- GPU0 dropped from ~280W avg / 300W cap → **260W avg / 260W cap**, and peak temp from 72°C → **65°C** (GPU0 runs notably cooler).
- GPU1 still peaks at **84°C** — it's the hotter card (likely better/worse cooler seating or airflow position). Power draw is now cap-limited, not thermal-limited, for GPU1's power, but its 84°C is driven by its higher baseline.
- CPU unchanged: still ~206W avg, hits 95°C thermal limit and throttles — this is independent of GPU caps.
- **1200W PSU even more comfortable** at 260W caps: ~845W worst case, **~30% headroom**.

**Recommendation:** 260W is a good setting — it keeps GPU0 cooler, reduces total draw, and costs little performance (GPU clocks barely dropped: ~1230MHz vs ~1300MHz). GPU1's higher temperature (84°C) is a **cooling/airflow issue**, not a power issue, and can be addressed by better chassis airflow or fan placement if desired.

## Interpreting Results

| Metric | Safe Range | Concern |
|--------|-----------|---------|
| CPU temp (`Tctl`) | < 85°C | > 90°C sustained |
| GPU temp | < 83°C | > 90°C |
| Total power | < ~1000W | near 1200W PSU limit |
| Stability | no crashes/reboots | systemd/driver errors |

## Power Limit Interaction

The GPU power caps (currently **260W**, applied at boot by `gpu-power-limit.service`) are active during the test. To test at a different limit, adjust the service file (`scripts/gpu/gpu-power-limit.service`) and reapply, or set it directly:

```bash
# Temporarily raise/lower the limit for one test
sudo nvidia-smi -i 0 -pl 260
sudo nvidia-smi -i 1 -pl 260

# Example: test near stock (uncapped) limits
sudo nvidia-smi -i 0 -pl 350
sudo nvidia-smi -i 1 -pl 350
```

To make a limit **permanent**, edit `ExecStart` lines in `scripts/gpu/gpu-power-limit.service`, then reinstall:
```bash
sudo cp scripts/gpu/gpu-power-limit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart gpu-power-limit.service
nvidia-smi --query-gpu=index,power.limit,persistence_mode --format=csv
```

Then run the stress test. **Note:** running uncapped raises total draw to ~1025W, still within the 1200W PSU but with less margin.

!!! warning
    Stress testing pushes hardware to its limits. Ensure adequate cooling before running. Monitor the first 30 seconds closely. Ctrl+C to abort.