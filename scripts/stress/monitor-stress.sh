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

# Detect RAPL package energy path (EPYC presents as intel-rapl here)
RAPL_ENERGY=""
for cand in /sys/class/powercap/intel-rapl:0/energy_uj /sys/class/powercap/*amd*/energy_uj; do
  [ -r "$cand" ] && RAPL_ENERGY="$cand" && break
done

# CSV header
echo "time_s,cpu_package_w,gpu0_w,gpu1_w,gpu0_util,gpu1_util,gpu0_mem,gpu1_mem,tctl_c,ccd1_c,ccd2_c" > "$LOG_FILE"

prev_energy=$(sudo cat "$RAPL_ENERGY" 2>/dev/null || echo 0)
prev_time=$(date +%s.%N)

for (( i=0; i<=DURATION; i+=INTERVAL )); do
  now=$(date +%s.%N)

  # --- CPU power via RAPL energy counter delta ---
  cur_energy=$(sudo cat "$RAPL_ENERGY" 2>/dev/null || echo 0)
  dt=$(awk -v a="$now" -v b="$prev_time" 'BEGIN{print a-b}')
  denergy=$(( cur_energy - prev_energy ))
  cpu_w=$(awk -v de="$denergy" -v dt="$dt" 'BEGIN{if(dt>0) printf "%.2f", de/1000000/dt; else printf "0"}')
  prev_energy=$cur_energy
  prev_time=$now

  # --- GPU stats (both cards) ---
  gpu=$(nvidia-smi --query-gpu=power.draw,utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null)
  gpu0_w=$(echo "$gpu" | sed -n '1p' | cut -d, -f1 | tr -d ' ')
  gpu1_w=$(echo "$gpu" | sed -n '2p' | cut -d, -f1 | tr -d ' ')
  gpu0_util=$(echo "$gpu" | sed -n '1p' | cut -d, -f2 | tr -d ' ')
  gpu1_util=$(echo "$gpu" | sed -n '2p' | cut -d, -f2 | tr -d ' ')
  gpu0_mem=$(echo "$gpu" | sed -n '1p' | cut -d, -f3 | tr -d ' ')
  gpu1_mem=$(echo "$gpu" | sed -n '2p' | cut -d, -f3 | tr -d ' ')

  # --- Temperatures ---
  tctl=$(sensors 2>/dev/null | grep -i tctl | awk '{print $2}' | tr -d '+°C')
  ccd1=$(sensors 2>/dev/null | grep -iE 'Tccd1|CCD1' | head -1 | awk '{print $2}' | tr -d '+°C')
  ccd2=$(sensors 2>/dev/null | grep -iE 'Tccd2|CCD2' | head -1 | awk '{print $2}' | tr -d '+°C')

  # --- Write row ---
  echo "$i,$cpu_w,$gpu0_w,$gpu1_w,$gpu0_util,$gpu1_util,$gpu0_mem,$gpu1_mem,$tctl,$ccd1,$ccd2" >> "$LOG_FILE"

  # --- Live display ---
  printf "Time=%4ss | CPU=%6sW | GPU0=%6sW(%3s%%) GPU1=%6sW(%3s%%) | Tctl=%sC\n" \
    "$i" "$cpu_w" "$gpu0_w" "$gpu0_util" "$gpu1_w" "$gpu1_util" "$tctl"

  sleep "$INTERVAL"
done

echo ""
echo "=== SUMMARY ==="
awk -F, 'NR>1 {
  c+=$2; g0+=$3; g1+=$4; t+=$9;
  if($3>mg0)mg0=$3; if($4>mg1)mg1=$4; if($2>mc)mc=$2
} END{
  n=NR-1;
  if(n<=0) exit;
  printf "Samples: %d\n", n;
  printf "Avg CPU pkg: %.1f W (max %.1f)\n", c/n, mc;
  printf "Avg GPU0: %.1f W (max %.1f)\n", g0/n, mg0;
  printf "Avg GPU1: %.1f W (max %.1f)\n", g1/n, mg1;
  printf "Avg Tctl: %.1f C\n", t/n;
}' "$LOG_FILE"

echo "Log saved to: $LOG_FILE"