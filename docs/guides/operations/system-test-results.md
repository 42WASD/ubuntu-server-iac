# System Test Results

This page is the **authoritative reference** for all measured test results on the server (`alpha`). Every figure below was captured from a real stress test on this exact hardware — it reflects the machine's true behavior, not manufacturer paper specs.

## Test Environment

| Component | Spec |
|-----------|------|
| Host | `alpha` (HUANANZHI H12D-8D motherboard, single socket populated) |
| CPU | AMD EPYC 7742 — 64 cores / 128 threads, 2.25 GHz base, ~3.4 GHz boost |
| RAM | 16 GB DDR4-2133 ECC RDIMM × 8 (SK Hynix `HMA42GR7MFR4N-TF`), 128 GB installed / ~123 GB usable |
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
| Memory | ✅ **All 8 slots populated** — 128 GB, 8-channel (channel H restored 2026-10-11, see below) |

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
| Workers | 8 × 10 GB (80 GB total) |
| Result | **PASSED** — 0 errors, 0 failures, 0 crashes |
| Bogo operations | ~58.5 million |
| Duration | 4 min |

Re-run on **2026-10-11** after channel H was restored (full 8-stick / 8-channel
configuration). `stress-ng --vm 8 --vm-bytes 10G --vm-method all --timeout 240s`:

```text
stress-ng: metrc: vm  58475455  240.45s  ...  243191.83 bogo ops/s
stress-ng: info:  passed: 8: vm (8)
stress-ng: info:  failed: 0
```

**Memory configuration (verified 2026-10-11 — all 8 slots):**

| Slot | Channel | Status |
|------|---------|--------|
| MM7 | Channel A | ✅ 16 GB |
| MM5 | Channel B | ✅ 16 GB |
| MM3 | Channel C | ✅ 16 GB |
| MM1 | Channel D | ✅ 16 GB |
| MM8 | Channel E | ✅ 16 GB |
| MM6 | Channel F | ✅ 16 GB |
| MM4 | Channel G | ✅ 16 GB |
| **MM2** | **Channel H** | ✅ **16 GB** (restored 2026-10-11) |

!!! note "Channel H history (2026-10-11)"
    Channel H (slot **MM2**) was **dead from the machine's first boot**: an extra
    **case standoff** mounted beneath the MM2 slot was shorting the board, so the
    firmware logged a fatal DRAM error and **mapped the channel out** — the system
    ran **7-channel / 112 GB** instead of 128 GB. Removing the standoff and clearing
    CMOS restored all 8 channels / **128 GB**. The exact replacement part, should a
    stick ever need swapping, is an **SK Hynix `HMA42GR7MFR4N-TF` 16 GB DDR4-2133
    2Rx4 ECC Registered RDIMM**. Full diagnosis in
    `_runbook/18-day-2-operations/` (DIMM channel-H failure).

**ECC note:** the memory is multi-bit ECC, so it can *detect and correct* errors. The passed pattern test confirms the sticks are fault-free; the earlier channel-H outage was a **board-level short, not a bad DIMM**. EDAC counters after the full stress + bandwidth suite: `ce_count=0`, `ue_count=0`.

---

## 3b. Memory Bandwidth Benchmark (8-channel, 2026-10-11)

Measured with a purpose-built **STREAM-style** benchmark
(`scripts/stress/stream-bench.c`, OpenMP, best-of-5 reps, 4 GiB per array =
12 GiB working set, all 128 threads).

!!! warning "Measure outside the Phase 9 CPU quota"
    The Phase 9 developer limits cap the owner slice at **8 cores**
    (`CPUQuota=800%`), which throttles a memory benchmark to ~6 GiB/s and makes
    the result meaningless. Run the benchmark **outside** the user slice:

    ```bash
    gcc -O3 -fopenmp -march=native scripts/stress/stream-bench.c -o stream-bench -lm
    sudo systemd-run --scope --slice=system -p CPUQuota=12800% \
      env OMP_NUM_THREADS=128 OMP_PROC_BIND=spread ./stream-bench 4096
    ```

### Sequential (streaming) bandwidth — all 128 threads

| Kernel | Operation | Bandwidth |
|--------|-----------|-----------|
| Copy | `c = a` | **67.1 GiB/s** (68,660 MiB/s) |
| Scale | `b = scalar × c` | **66.6 GiB/s** (68,236 MiB/s) |
| Add | `c = a + b` | **74.3 GiB/s** (76,065 MiB/s) |
| Triad | `a = b + scalar × c` | **75.3 GiB/s** (77,085 MiB/s) |

The **Triad** figure is the standard STREAM headline number: **~75 GiB/s**.

### Random-access bandwidth — all 128 threads

Cache-hostile permutation walk over 4 GiB (each element touched once per rep):

| Kernel | Operation | Bandwidth |
|--------|-----------|-----------|
| RandR | random read | **7.6 GiB/s** useful payload (~15 GiB/s raw traffic) |
| RandW | random write (scattered stores) | **5.1 GiB/s** |
| RandRW | random read-modify-write | **5.3 GiB/s** |

Random access is **~10× slower** than streaming — expected, because a random
8-byte access wastes a full 64-byte cache line, and the DRAM page/bank locality
that streaming relies on is gone. This is the number that matters for
pointer-chasing workloads (graph/LLM KV-cache, hash tables), not the streaming
figure.

### Single-thread baseline (for scaling context)

| Kernel | 1 thread | 128 threads | Scaling |
|--------|----------|-------------|---------|
| Copy | 17.9 GiB/s | 67.1 GiB/s | 3.7× |
| Triad | 20.2 GiB/s | 75.3 GiB/s | 3.7× |
| RandR | 0.8 GiB/s | 7.6 GiB/s | 9.7× |

A single EPYC 7742 core already extracts ~18–20 GiB/s — about **25% of the full
75 GiB/s** — so most memory-bound work saturates with a handful of cores.

### Reference: vendor expectation

The EPYC 7742 (8-channel DDR4-3200 capable, but this system runs **DDR4-2133**)
has a theoretical peak of `8 channels × 8 bytes × 2 (DDR) × 2133 MT/s`
= **~273 GB/s ≈ 254 GiB/s**. Measured streaming **75 GiB/s** is ~**30% of
theoretical peak**, which is normal for real STREAM on DDR4-2133 with a single
socket and the low clock this part runs (2.25 GHz base). The 8-channel
configuration is confirmed working — a 7-channel config would be ~12% lower.

---

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
- Cost little performance — AI inference is memory-bandwidth-bound (see [GPU Power Limiting](../hardware/gpu-power-limit-guide.md)).

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
| Hardware inventory | ✅ All 8 memory slots populated (128 GB, 8-channel) |

---

See the [System Stress Test](stress-test-guide.md) guide for how to reproduce these tests, and the [System Performance](system-performance.md) summary for a condensed version.