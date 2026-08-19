# System Test Results

This page is the **authoritative reference** for all measured test results on the server (`alpha`). Every figure below was captured from a real stress test on this exact hardware — it reflects the machine's true behavior, not manufacturer paper specs.

## Test Environment

| Component | Spec |
|-----------|------|
| Host | `alpha` (HUANANZHI H12D-8D motherboard, single socket populated) |
| CPU | AMD EPYC 7742 — 64 cores / 128 threads, 2.25 GHz base, ~3.4 GHz boost |
| RAM | 16 GB DDR4-2133 ECC RDIMM × 7 (SK Hynix `HMA42GR7MFR4N-TF`), 112 GB installed / ~107 GB usable |
| GPU 0 | NVIDIA RTX 3090 (24 GB GDDR6X) — top PCIe slot (`0000:81:00.0`) |
| GPU 1 | NVIDIA RTX 3090 (24 GB GDDR6X) — `0000:C4:00.0` |
| PSU | 1200 W |
| OS | Ubuntu Server 26.04 LTS |
| NVIDIA driver | 595.71.05 |
| GPU power cap | **260 W** (both, applied at boot by `gpu-power-limit.service`) |

### Hardware validation status

| Subsystem | Status |
|-----------|--------|
| CPU cores | ✅ All 64 cores / 128 threads online & enabled |
| GPUs | ✅ Both RTX 3090 detected, drivers healthy |
| Memory | ⚠️ **7 of 8 slots populated** — MM2 / Channel H is empty (see below) |

---

## 1. CPU Stress Test

Run: `stress-ng --cpu $(nproc) --cpu-method matrixprod` across all 128 threads.

| Metric | Average | Peak |
|--------|---------|------|
| Package power (RAPL) | ~206 W | ~287 W* |
| Core clock (all-core avg) | ~2673 MHz | ~2800 MHz |
| `Tctl` temperature | ~85°C | **95°C** (thermal limit) |
| Threads exercised | 128/128 | 100% |

\* The ~287 W figure is the power-up transient; sustained load settles at **~206 W** (EPYC 7742 TDP).

**Notes**
- All 128 threads reached 100% utilization (`%Cpu(s): 99.8 us`).
- The CPU runs **right at its 95°C thermal limit** under sustained all-core load and **throttles** to protect itself. This is normal and safe (the EPYC self-regulates), but the cooler is adequate rather than over-provisioned. Do **not** raise the power limit or overclock on stock cooling.

---

## 2. GPU Stress Test

Run: **gpu-burn** (CUDA) on both RTX 3090s simultaneously, **260 W** cap each.

| Metric | GPU 0 | GPU 1 |
|--------|-------|-------|
| Power (avg) | ~248 W | ~247 W |
| Power (max) | 260 W | 260 W |
| SM clock (avg) | ~1198 MHz | ~1091 MHz |
| SM clock (peak) | 1230 MHz | 1065 MHz |
| Temperature (avg) | ~61°C | ~77°C |
| Temperature (peak) | **65°C** | **84°C** |
| gpu-burn throughput | ~20,000–22,000 Gflop/s | ~16,000–17,000 Gflop/s |
| **Errors** | **0** | **0** |

**Notes**
- **Zero errors** over the full 180 s test on both cards — compute is fully stable.
- GPU 0 (top slot) runs much cooler (65°C peak) than GPU 1 (84°C peak). GPU 1's higher temperature is a **cooling/airflow** characteristic of its position, not a power issue (both are at the same 260 W cap and power draw).
- GPU 0 is the faster card (~21,000 Gflop/s vs ~16,500), consistent with its lower temperature.

---

## 3. Memory Stress Test

Run: `stress-ng --vm` using the **`all`** method set (includes the classic fault-detection patterns `galpat`, `rowhammer`, `walk`, `prime`, `checkerboard`, `move-inv`) across the installed RAM.

| Metric | Result |
|--------|--------|
| Stressor | `vm` |
| Memory patterns | `all` |
| Workers | 8 |
| Result | **PASSED** — 0 errors, 0 failures, 0 crashes |
| Bogo operations | ~70.2 million |
| Duration | 5 min |

**Memory configuration (important):**

| Slot | Channel | Status |
|------|---------|--------|
| MM7 | Channel A | ✅ 16 GB |
| MM5 | Channel B | ✅ 16 GB |
| MM3 | Channel C | ✅ 16 GB |
| MM1 | Channel D | ✅ 16 GB |
| MM8 | Channel E | ✅ 16 GB |
| MM6 | Channel F | ✅ 16 GB |
| MM4 | Channel G | ✅ 16 GB |
| **MM2** | **Channel H** | **❌ EMPTY** |

!!! warning "One stick is missing"
    The board has **8 slots** but only **7 are populated**. **MM2 / Channel H is empty**, so the system has **112 GB installed (~107 GB usable)** instead of the full **128 GB / 8-channel** config. The exact replacement part is an **SK Hynix `HMA42GR7MFR4N-TF` 16 GB DDR4-2133 2Rx4 ECC Registered RDIMM**. See the [hardware notes in the performance guide](system-performance.md) for how to source it. Memory runs in **7-channel** mode until it is added.

**ECC note:** the memory is multi-bit ECC, so it can *detect and correct* errors. The passed pattern test confirms the 7 present sticks are fault-free.

---

## 4. Power Supply Validation (1200 W)

Full **simultaneous** CPU (128 threads) + GPU (both 3090s) stress at **260 W** GPU caps.

| Metric | Value |
|--------|-------|
| Total package draw (avg) | **~701 W** |
| CPU | ~206 W |
| GPU 0 | ~248 W |
| GPU 1 | ~247 W |
| Estimated rest of system | ~100 W (RAM, board, storage) |
| **Worst-case system peak** | **~850 W** |
| **PSU headroom** | **~30%** |

**Verdict: the 1200 W PSU is comfortably adequate.** Even at worst-case simultaneous load, the system draws far less than the PSU can supply, with ~30% headroom. No crashes, no reboots, no GPU dropout over the entire test.

---

## 5. Power-Limit Trade-off (300 W vs 260 W)

| Setting | GPU0 avg | GPU1 avg | GPU0 peak temp | GPU1 peak temp | Total pkg |
|---------|----------|----------|----------------|----------------|-----------|
| 300 W cap | 280 W | 263 W | 72°C | 85°C | ~750 W |
| **260 W cap** | **248 W** | **247 W** | **65°C** | **84°C** | **~701 W** |

Lowering to 260 W:
- Cut GPU0's temperature 72 → **65°C**.
- Reduced total package draw ~750 → **~701 W** (more PSU headroom).
- Cost little performance — AI inference is memory-bandwidth-bound (see [GPU Power Limiting](gpu-power-limit-guide.md)).

**260 W is the recommended long-term setting.**

---

## 6. System Verification Summary

| Test | Result |
|------|--------|
| CPU all-cores load | ✅ All 128 threads at 100%, no instability |
| GPU compute (both cards) | ✅ Zero gpu-burn errors |
| Memory pattern test | ✅ 0 errors, all patterns passed |
| Power supply validation | ✅ ~700 W worst case, ~30% headroom |
| Thermal | ⚠️ CPU hits 95°C limit & throttles (normal); GPU1 at 84°C (airflow) |
| Hardware inventory | ⚠️ MM2 memory slot empty (1 of 8 sticks missing) |

---

See the [System Stress Test](stress-test-guide.md) guide for how to reproduce these tests, and the [System Performance](system-performance.md) summary for a condensed version.