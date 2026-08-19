# GPU Power Limiting

This guide documents how the **2 × NVIDIA RTX 3090** GPUs on the server (`alpha`) are power-limited to **260W** each and kept persistent across reboots using a **systemd service**.

## Why Limit GPU Power?

The RTX 3090 ships with a **350W** default power limit. In this particular system, GPU 0 was found running at **390W** (above stock — likely from a prior overclock/undervolt tool). Capping both cards at **260W** (the AI efficiency sweet spot) delivers:

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

Both cards support a **260W** target.

## Service File

The service definition is committed to the repo at:

```
scripts/gpu/gpu-power-limit.service
```

```ini title="scripts/gpu/gpu-power-limit.service"
[Unit]
Description=Set NVIDIA GPU power limits to 260W and enable persistence mode
After=multi-user.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
RemainAfterExit=yes
# Persistence mode keeps the driver loaded so power limits stay applied.
ExecStart=/usr/bin/nvidia-smi -pm 1
# Apply a 260W power limit to both RTX 3090 GPUs.
ExecStart=/usr/bin/nvidia-smi -i 0 -pl 260
ExecStart=/usr/bin/nvidia-smi -i 1 -pl 260

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

Check that both GPUs report a **260W** limit and **Enabled** persistence mode:

```bash
nvidia-smi --query-gpu=index,name,power.limit,persistence_mode --format=csv
```

Expected output:

```text
index, name, power.limit [W], persistence_mode
0, NVIDIA GeForce RTX 3090, 260.00 W, Enabled
1, NVIDIA GeForce RTX 3090, 260.00 W, Enabled
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

## The 260W "Sweet Spot" for AI Workloads

Independent power-tuning experiments on the RTX 3090 for **LLM, vision, speech-to-text (TTS), and diffusion** workloads consistently converge on a narrow efficiency plateau around **250–300W**, with **~260W being a commonly cited sweet spot**. Above that plateau the card keeps consuming more power but returns rapidly diminishing performance; below it you start giving up measurable throughput.

### Why 260W hits the sweet spot

- **Memory-bandwidth bound inference.** Local LLM/vision/TTS inference is overwhelmingly limited by the 3090's memory bandwidth (~936 GB/s), not raw compute. At low batch sizes the compute cores idle waiting for VRAM, so feeding them more power just generates heat. This is why power-limiting an inference workload saves a large fraction of power for a very small throughput cost.
- **The plateau effect.** Across power scaling tests (e.g. 150W→350W), output tokens-per-second rises steeply up to roughly the 250–270W region, then flattens out. Between ~260W and 350W the curve is nearly flat, so the extra ~90W buys almost nothing for inference.
- **Two cards in this server.** Every watt above the sweet spot is doubled because `alpha` carries **two RTX 3090s**. Dropping both cards from 350W to 260W removes up to **180W of heat from the chassis** while preserving the large majority of inference performance — which matters for the shared 1200W PSU and VRM temperatures.
- **Consistency across workload families.** The same plateau shows up for LLM, vision, TTS, and diffusion workloads, so a single 260W target is a good default rather than something you must retune per model.

### How the sweet spot maps to this guide

| Limit | Effect | Where 260W sits |
|-------|--------|-----------------|
| 350 W | Stock — full power, most heat | Far above the plateau |
| 300 W | Conservative cap | Just above the plateau |
| **260 W** | **Active AI sweet spot (current setting)** | **Peak efficiency-per-watt plateau** |
| 250 W | Aggressive — larger perf hit, maximum savings | Bottom of the plateau |
| 220 W | Heavily capped — biggest savings | Below the plateau, more perf lost |

260W keeps you comfortably inside the efficiency plateau for AI workloads while cutting power and heat well below stock.

### Currently applied

260W is now the **active default**, applied at every boot by the systemd service. The service file in the repo is already set to `-pl 260`.

!!! note
    GPU 0 supports 100–480W; GPU 1 supports 100–365W. A 260W target is comfortably within both cards' supported ranges.

## Sources

- **RTX3090 Power Tuning Results on LLM, Vision, TTS, and Diffusion** — r/LocalLLaMA. Recommends setting the 3090's power limit to ~250–300W to get excellent performance while saving on the order of 100W per card:  
  <https://www.reddit.com/r/LocalLLaMA/comments/1egvoqj/rtx3090_power_tuning_results_on_llm_vision_tts/>
- **GPU Power Tuning for AI Workloads** — CJ's Workshop (YouTube). Benchmarks a single RTX 3090 from 150W to 350W in 5W increments across four workload types (LLM, vision, speech-to-text, diffusion), showing how each responds to its power envelope: <https://www.youtube.com/watch?v=vshdD1Q0Mgs>

These two sources are the primary basis for the **260W sweet spot** recommended in this guide.