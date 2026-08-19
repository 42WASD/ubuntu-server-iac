#!/usr/bin/env bash
# monitor-stress.sh
#
# Monitors and logs CPU + GPU power, temperature, and utilization during a
# stress test. Outputs a timestamped CSV log plus a live readout.
#
# Usage:
#   ./monitor-stress.sh [duration_seconds] [interval_seconds]
#
# Examples:
#   ./monitor-stress.sh 60        # log for 60s, sample every 1s
#   ./monitor-stress.sh 120 2     # log for 120s, sample every 2s
#
# Dependencies: nvidia-smi, lm-sensors (sensors), sudo for RAPL power read.

set -u

DURATION="${1:-60}"
INTERVAL="${2:-1}"

LOG_FILE="stress-monitor-$(date +%Y%m%d-%H%M%S).csv"
echo "Logging to: $LOG_FILE"

# Detect RAPL package energy path (EPYC presents as intel-rapl here).
# Energy counters are root-readable, so we verify via sudo instead of -r.
RAPL_ENERGY=""
for cand in /sys/class/powercap/intel-rapl:0/energy_uj /sys/class/powercap/intel-rapl:0:0/energy_uj /sys/class/powercap/*amd*/energy_uj; do
  if [ -e "$cand" ] && sudo cat "$cand" >/dev/null 2>&1; then
    RAPL_ENERGY="$cand"
    break
  fi
done
[ -n "$RAPL_ENERGY" ] || { echo "WARNING: no readable RAPL energy counter found; CPU power will be 0"; }
echo "Using RAPL counter: ${RAPL_ENERGY:-none}"

# RAPL energy counters wrap (32-bit near 2^32 uJ, ~20s at full CPU load).
# Read the max range so we can correctly unwrap negative deltas.
if [ -n "$RAPL_ENERGY" ]; then
  WRAP_MAX=$(cat "${RAPL_ENERGY%/energy_uj}/max_energy_range_uj" 2>/dev/null)
fi
WRAP_MAX="${WRAP_MAX:-4294967296}"   # fallback 2^32 uJ

# CSV header
echo "time_s,cpu_package_w,cpu_avg_mhz,gpu0_w,gpu1_w,gpu0_util,gpu1_util,gpu0_mem,gpu1_mem,gpu0_sm_mhz,gpu1_sm_mhz,gpu0_mem_mhz,gpu1_mem_mhz,gpu0_temp_c,gpu1_temp_c,tctl_c,ccd1_c,ccd2_c" > "$LOG_FILE"

prev_energy=$(sudo cat "$RAPL_ENERGY" 2>/dev/null || echo 0)
prev_time=$(date +%s.%N)

for (( i=0; i<=DURATION; i+=INTERVAL )); do
  now=$(date +%s.%N)

  # --- CPU power via RAPL energy counter delta ---
  cur_energy=$(sudo cat "$RAPL_ENERGY" 2>/dev/null || echo 0)
  dt=$(awk -v a="$now" -v b="$prev_time" 'BEGIN{print a-b}')
  denergy=$(( cur_energy - prev_energy ))
  # Correct for 32-bit counter wraparound: if delta is negative, add wrap range.
  if [ "$denergy" -lt 0 ]; then
    denergy=$(( denergy + WRAP_MAX ))
  fi
  cpu_w=$(awk -v de="$denergy" -v dt="$dt" 'BEGIN{if(dt>0) printf "%.2f", de/1000000/dt; else printf "0"}')
  prev_energy=$cur_energy
  prev_time=$now

  # --- CPU average clock (all cores, kHz -> MHz) ---
  cpu_mhz=$(awk '{s+=$1;n++} END{printf "%.0f", (n>0 ? s/n/1000 : 0)}' \
    /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null)

  # --- GPU stats (both cards) ---
  gpu=$(nvidia-smi --query-gpu=power.draw,utilization.gpu,memory.used,clocks.sm,clocks.mem,temperature.gpu --format=csv,noheader,nounits 2>/dev/null)
  gpu0_w=$(echo "$gpu" | sed -n '1p' | cut -d, -f1 | tr -d ' ')
  gpu1_w=$(echo "$gpu" | sed -n '2p' | cut -d, -f1 | tr -d ' ')
  gpu0_util=$(echo "$gpu" | sed -n '1p' | cut -d, -f2 | tr -d ' ')
  gpu1_util=$(echo "$gpu" | sed -n '2p' | cut -d, -f2 | tr -d ' ')
  gpu0_mem=$(echo "$gpu" | sed -n '1p' | cut -d, -f3 | tr -d ' ')
  gpu1_mem=$(echo "$gpu" | sed -n '2p' | cut -d, -f3 | tr -d ' ')
  gpu0_sm_mhz=$(echo "$gpu" | sed -n '1p' | cut -d, -f4 | tr -d ' ')
  gpu1_sm_mhz=$(echo "$gpu" | sed -n '2p' | cut -d, -f4 | tr -d ' ')
  gpu0_mem_mhz=$(echo "$gpu" | sed -n '1p' | cut -d, -f5 | tr -d ' ')
  gpu1_mem_mhz=$(echo "$gpu" | sed -n '2p' | cut -d, -f5 | tr -d ' ')
  gpu0_temp=$(echo "$gpu" | sed -n '1p' | cut -d, -f6 | tr -d ' ')
  gpu1_temp=$(echo "$gpu" | sed -n '2p' | cut -d, -f6 | tr -d ' ')

  # --- Temperatures ---
  tctl=$(sensors 2>/dev/null | grep -i tctl | awk '{print $2}' | tr -d '+°C')
  ccd1=$(sensors 2>/dev/null | grep -iE 'Tccd1|CCD1' | head -1 | awk '{print $2}' | tr -d '+°C')
  ccd2=$(sensors 2>/dev/null | grep -iE 'Tccd2|CCD2' | head -1 | awk '{print $2}' | tr -d '+°C')

  # --- Write row ---
  echo "$i,$cpu_w,$cpu_mhz,$gpu0_w,$gpu1_w,$gpu0_util,$gpu1_util,$gpu0_mem,$gpu1_mem,$gpu0_sm_mhz,$gpu1_sm_mhz,$gpu0_mem_mhz,$gpu1_mem_mhz,$gpu0_temp,$gpu1_temp,$tctl,$ccd1,$ccd2" >> "$LOG_FILE"

  # --- Live display ---
  printf "Time=%4ss | CPU=%6sW(%4sMHz) | GPU0=%5sW(%3s%%,%4sMHz,%sC) GPU1=%5sW(%3s%%,%4sMHz,%sC) | Tctl=%sC\n" \
    "$i" "$cpu_w" "$cpu_mhz" "$gpu0_w" "$gpu0_util" "$gpu0_sm_mhz" "$gpu0_temp" \
    "$gpu1_w" "$gpu1_util" "$gpu1_sm_mhz" "$gpu1_temp" "$tctl"

  sleep "$INTERVAL"
done

echo ""
echo "=== SUMMARY ==="
awk -F, 'NR>1 {
  c+=$2; g0+=$4; g1+=$5; t+=$16;
  cmhz+=$3; g0m+=$10; g1m+=$11;
  g0t+=$14; g1t+=$15;
  if($4>mg0)mg0=$4; if($5>mg1)mg1=$5; if($2>mc)mc=$2; if($16>mt)mt=$16
} END{
  n=NR-1;
  if(n<=0) exit;
  printf "Samples: %d\n", n;
  printf "Avg CPU pkg: %.1f W (max %.1f), avg %.0f MHz\n", c/n, mc, cmhz/n;
  printf "Avg GPU0: %.1f W (max %.1f), avg %.0f MHz, avg %.1f C\n", g0/n, mg0, g0m/n, g0t/n;
  printf "Avg GPU1: %.1f W (max %.1f), avg %.0f MHz, avg %.1f C\n", g1/n, mg1, g1m/n, g1t/n;
  printf "Avg Tctl: %.1f C (max %.1f)\n", t/n, mt;
}' "$LOG_FILE"

echo "Log saved to: $LOG_FILE"