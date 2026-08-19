# System Performance Under Load

This page documents the **measured real-world performance** of the server (`alpha`) under heavy simultaneous load. All figures below come from actual stress-test runs on this exact hardware, so they reflect the machine's true sustained behavior — not manufacturer paper specs.

## Hardware Summary

| Component | Spec |
|-----------|------|
| CPU | AMD EPYC 7742 — 64 cores / 128 threads, 2.25 GHz base, ~3.4 GHz boost |
| RAM | 7 × 16 GB DDR4-2133 ECC (SK Hynix) — 107 GB usable, multi-bit ECC |
| GPU 0 | NVIDIA RTX 3090 (24 GB GDDR6X), top PCIe slot |
| GPU 1 | NVIDIA RTX 3090 (24 GB GDDR6X) |
| PSU | 1200 W |
| Motherboard | HUANANZHI H12D-8D (single socket populated) |

The GPUs are power-capped at **260W each** (see the [GPU Power Limiting guide](gpu-power-limit-guide.md)) to sit on the AI efficiency sweet spot.

## Measured Performance Under Full Load

The table below shows **sustained averages** during a full 180-second simultaneous CPU + GPU stress test (all 128 CPU threads + both GPUs at 100%), with both GPUs at their 260W cap.

| Metric | Average | Peak |
|--------|---------|------|
| **CPU power** (package RAPL) | ~206 W | ~287 W* |
| **CPU clock** (all cores avg) | ~2673 MHz | ~2800 MHz |
| **CPU temp** (`Tctl`) | ~85°C | **95°C** (thermal limit) |
| **GPU 0 power** | ~248 W | 260 W |
| **GPU 0 SM clock** | ~1198 MHz | 1230 MHz |
| **GPU 0 temp** | ~61°C | 65°C |
| **GPU 1 power** | ~247 W | 260 W |
| **GPU 1 SM clock** | ~1091 MHz | 1065 MHz |
| **GPU 1 temp** | ~77°C | 84°C |
| **gpu-burn throughput** | ~20,000–22,000 Gflop/s (GPU 0), ~16,000–17,000 Gflop/s (GPU 1) | — |
| **gpu-burn errors** | **0** | 0 |
| **Total package draw** | **~701 W** | — |

\* The ~287 W CPU figure is the power-up transient; sustained load settles to **~206 W** at the EPYC 7742 TDP.

### What these numbers mean

- **Compute stability is perfect.** `gpu-burn` ran the full 180 s on both GPUs with **zero errors**, and the system never crashed, rebooted, or dropped a GPU — even at sustained max load.
- **The 1200 W PSU has comfortable headroom.** Total worst-case package draw is ~700–750 W. Adding the estimated ~100 W for RAM, motherboard, and storage, the whole machine peaks around **~850 W**, leaving the 1200 W PSU with roughly **30% headroom**. See the [Stress Test guide](stress-test-guide.md) for the full power-budget breakdown.
- **The CPU is the thermal hotspot.** It runs at the ~95°C thermal limit under sustained all-core load and throttles to protect itself. This is normal and safe (the EPYC self-regulates) but means the cooler is adequate, not over-provisioned.

## Memory Performance & Validation

The 7 memory sticks were validated with a comprehensive stress test:

- **Config:** 7 × 16 GB DDR4-2130 ECC, running on 8 channels (channels A–G populated, H empty), 112 GB installed / ~107 GB usable.
- **Validation:** `stress-ng --vm` with the `all` memory-pattern set (including the classic fault-detection patterns: `galpat`, `rowhammer`, `walk`, `prime`, `checkerboard`, `move-inv`) across ~90 GB of the installed RAM.
- **Result:** **PASSED** — 0 errors, 0 failures across all memory patterns.

### Why this matters

Memory errors are silent and cumulative: a single bad DIMM can corrupt data and produce intermittent application crashes that are very hard to diagnose. Running the full set of bit-pattern tests across **all** installed memory confirms every stick is fault-free. This is especially important on an ECC system — the ECC can *detect* and *correct* errors, but a truly defective stick should be caught and replaced before it causes corrupted results or repeated ECC-corrected events under real workload.

## Power-Limit Trade-off (300 W vs 260 W)

Because the GPUs were capped at both 300 W and 260 W in separate tests, we have direct data on the trade-off:

| Setting | GPU0 avg | GPU1 avg | GPU0 peak temp | GPU1 peak temp | Total pkg |
|---------|----------|----------|----------------|----------------|-----------|
| 300 W cap | 280 W | 263 W | 72°C | 85°C | ~750 W |
| **260 W cap** | **260 W** | **260 W** | **65°C** | **84°C** | **~701 W** |

Lowering the cap to 260 W:
- Cut GPU0's temperature from 72 °C → **65 °C** (the coolest card got much cooler once power-limited).
- Reduced total package draw from ~750 W → **~701 W**, giving the PSU more headroom.
- Cost very little performance — GPU clocks only dropped slightly (~1190 vs ~1230 MHz), and AI inference is memory-bandwidth-bound anyway (see [GPU Power Limiting](gpu-power-limit-guide.md)).
- GPU1 stays at ~84 °C at both settings — it's the warmer card regardless, a cooling/airflow characteristic rather than a power/limit issue.

**Recommendation:** 260 W is the right long-term setting — it keeps GPU0 cooler, trims total draw, and barely costs any performance.

## Conclusion

This system is **stable and well-provisioned**:

- **Compute:** Both RTX 3090s sustain full load indefinitely with zero errors.
- **CPU:** All 128 threads run at ~2.6–2.8 GHz sustained; thermals are the only limiter (expected, normal).
- **Memory:** All 7 sticks pass comprehensive pattern testing — no faults.
- **Power:** The 1200 W PSU has ~30% headroom at worst case, so it is **more than adequate**.

See the [Stress Testing Guide](stress-test-guide.md) for the full procedure to reproduce these measurements.