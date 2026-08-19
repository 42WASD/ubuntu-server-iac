#!/usr/bin/env bash
# stress-test.sh
#
# Runs a full simultaneous CPU + GPU stress test to validate system stability
# and power delivery on the 1200W PSU.
#
# Usage:
#   ./stress-test.sh [duration_seconds]
#
# Examples:
#   ./stress-test.sh 120     # 2 minute full burn
#   ./stress-test.sh 600      # 10 minute full burn (recommended)
#
# What it does:
#   1. Spawns stress-ng on all CPU threads (max load, FPU-heavy method)
#   2. Spawns gpu-burn on BOTH RTX 3090s simultaneously
#   3. Runs monitor-stress.sh alongside to log power/thermal data
#   4. Kills all stressors when done and prints the log
#
# Dependencies: stress-ng, gpu-burn (on PATH), nvidia-smi, lm-sensors
# Run with sudo for full CPU affinity + RAPL reads.

set -u

DURATION="${1:-300}"
GPU_BURN="${GPU_BURN:-/usr/local/bin/gpu_burn}"
GPU_KERNEL="${GPU_KERNEL:-/usr/local/bin/compare.fatbin}"

echo "=== STARTING FULL SYSTEM STRESS TEST (${DURATION}s) ==="
echo "Target: EPYC 7742 (CPU) + 2x RTX 3090 (GPU) on 1200W PSU"
echo "GPU power caps: $(nvidia-smi --query-gpu=power.limit --format=csv,noheader | tr '\n' ',') W (systemd service applies at boot)"
echo ""

# Sanity checks
command -v stress-ng >/dev/null || { echo "ERROR: stress-ng not installed"; exit 1; }
if [ ! -x "$GPU_BURN" ]; then echo "ERROR: gpu_burn not found at $GPU_BURN"; exit 1; fi

# Number of CPU threads (use all 128)
NCORES=$(nproc)
echo "Starting stress-ng on ${NCORES} threads..."

# Launch CPU stress (all threads, FPU-heavy method that maximizes power draw)
stress-ng --cpu "$NCORES" --cpu-method matrixprod --timeout "${DURATION}s" &
CPU_PID=$!

# Launch GPU stress on all GPUs (specify compare kernel path explicitly)
"$GPU_BURN" -c "$GPU_KERNEL" "$DURATION" &
GPU_PID=$!

# Launch the monitor (samples power + thermals every 2s) in background
./scripts/stress/monitor-stress.sh "$DURATION" 2 &
MONITOR_PID=$!

echo "Stressors launched. CPU pid=$CPU_PID, GPU pid=$GPU_PID"
echo "Monitor pid=$MONITOR_PID — live readings below:"
echo "---------------------------------------------------"

# Wait for all to finish
wait "$CPU_PID" 2>/dev/null
wait "$GPU_PID" 2>/dev/null
wait "$MONITOR_PID" 2>/dev/null

echo ""
echo "=== STRESS TEST COMPLETE ==="
echo "If the system stayed stable (no crashes, temps < 90C, power < 1200W wall), your PSU is adequate."
echo "See the latest stress-monitor-*.csv in the CWD for full data."