---
phase: 18-day-2-operations/host-hardware
---

# Runbook — DIMM channel H failure (case standoff shorting the MM2 slot)

**Symptom:** the machine reported **112 GiB** instead of 128 GiB, and slot
**MM2 / Channel H** showed `No Module Installed` in `dmidecode` even though a
DIMM was physically seated. This had been true since the machine's **first
boot** — it was never a "missing stick".

**Root cause (confirmed):** an extra **case standoff** mounted on the
motherboard tray sat directly **beneath the MM2 (Channel H) DDR4 slot**. With no
matching hole in the board, it pressed into the PCB and **shorted the channel**.
The firmware logged a **fatal DRAM error** and **mapped the channel out**, which
is why the slot read as empty and the OS saw only 7 channels.

**Fix:** remove the standoff, then clear the latched map-out (CMOS clear).

> This page is the go-to reference for "one memory channel missing / a DIMM
> shows as absent / unexplained host freeze on an EPYC board".

## Symptom signature

- `free -h` / `lsmem` show less RAM than installed (here 112 vs 128 GiB).
- `dmidecode -t 17` shows the slot as `Size: No Module Installed`, `Type: Unknown`.
- Firmware error record in `dmesg` / `journalctl -k` (read on the *next* boot):

  ```text
  BERT: Error records from previous boot:
  [Hardware Error]: event severity: fatal
  [Hardware Error]:  fru_text: DIMM Locate:  P0H0      <- P0 = socket 0, H = channel H
  [Hardware Error]:   section_type: memory error
  [Hardware Error]:    error_status: Storage error in DRAM memory (0x0000000000040400)
  [Hardware Error]:   node:0 card:4 module:0
  [Hardware Error]:   error_type: 15, physical memory map-out event
  ```

- `amdfam17h`/`amd64_edac` logs may still show the channel's chip-selects
  (`UMC7 ... 2 × 8192MB`) even though firmware excludes the range from e820 —
  the controller "sees" the channel, the firmware refuses to use it.

## Diagnostic commands

```bash
# what the OS actually has
free -h
lsmem --summary

# per-slot truth (serial/part number per slot)
sudo dmidecode -t 17 | grep -E 'Locator:|Bank Locator:|Size:|Serial Number:|Part Number:'

# the firmware's own error record (appears on the boot AFTER the fault)
sudo dmesg | grep -iE -A3 'BERT|Hardware Error|fru_text|map-out'

# memory-controller view vs firmware view
sudo dmesg | grep -E 'UMC[0-9] chip selects|amd64: MC:'
grep MemTotal /proc/meminfo

# ECC error counters
cat /sys/devices/system/edac/mc/mc0/{ce_count,ue_count}
```

## Decoding the locator

`fru_text: DIMM Locate: P0H0` → **P**rocessor 0, channel **H**, DIMM 0.
Map channel letters to the board silkscreen: on the H12D-8D, channel H is slot
**MM2** (SMBIOS `Bank Locator: P0 CHANNEL H`). The 8 slots map as
`MM7=A MM5=B MM3=C MM1=D MM8=E MM6=F MM4=G MM2=H`.

## Fix procedure (verified 2026-10-11)

```bash
# 1) Record boot config first — a CMOS clear resets UEFI boot entries
efibootmgr

# 2) Shut down cleanly, then at the machine:
sudo poweroff
#    - unplug the PSU
#    - hold the power button ~30 s to drain
#    - remove the case panel and inspect UNDER the board near the dead slot

# 3) PHYSICAL: remove any standoff that does not line up with a board mounting
#    hole (E-ATX-capable cases often ship extra standoffs for E-ATX boards).
#    Look for a dimple/dent in the PCB under the slot area.
#    Also check the screws near the DIMM bank are not over-tightened.

# 4) Clear the latched map-out: short CLR_CMOS pins ~10 s, or pull the coin
#    battery for a few minutes, with the PSU unplugged.

# 5) Reassemble, power on, and verify
free -h                                       # expect the full installed amount
sudo dmidecode -t 17 | grep -A4 'Locator: MM2'  # expect a real part number
sudo dmesg | grep -iE 'BERT|P0H'                # expect no NEW fatal record
```

**Result on `alpha`:**

```text
before: free -h -> 107Gi total   MM2: No Module Installed   BERT: fatal P0H0 map-out
after : free -h -> 123Gi total   MM2: SK Hynix HMA42GR7MFR4N-TF 16GB (s/n 24D93009)
        lsmem -> 130G online      EDAC ce_count=0 ue_count=0   no new BERT record
```

## Notes / caveats

- **Two variables were changed at once** on `alpha` (the stick was swapped *and*
  the standoff removed), so strictly the fix cannot be attributed to one alone.
  The standoff was **physically confirmed** beneath MM2 and matches the
  documented failure class, so it is treated as the root cause.
- **This class is documented on EPYC boards generally.** Supermicro H11SSL
  owners reported DIMMH1 (channel H, beside the 24-pin power connector) dead
  from an identical standoff short; H12SSL owners fixed the same symptom by
  loosening screws near the DIMM slots. EPYC single-channel failures are also
  classically caused by **CPU socket mounting pressure / bent pins** — check
  that if a standoff is not found.
- **The firmware's map-out is correct behaviour, not a bug.** It disables the
  channel to keep the machine bootable. It must be cleared (CMOS) after the
  physical fault is fixed, or the channel stays disabled even with a good stick.
- **This board ignores `systemctl reboot --firmware-setup`** — the UEFI
  `OsIndications` variable stays set and the firmware boots straight to the OS.
  There is no BMC/IPMI (the AST2500 module is not installed), so BIOS access
  requires a physical display; a CMOS clear is the headless alternative.

## Related: the 2026-08-26 host freeze

The BERT fatal `P0H0` record was dated to the boot that **ended abruptly on
2026-08-26 06:44:40** (kernel log not flushed — classic hard lockup). The
Phase 8.6 runbook had attributed that freeze to a `dotnet publish` writing to
RAM-backed `/tmp` with swap disabled. That path contributed, but the **fatal
DRAM error is the more probable trigger** — see the annotation in
`_runbook/03-build-the-host/phase-08-system-tuning.md` §8.6.

### Boot-by-boot BERT timeline (proof the fix worked)

The fatal `P0H0` record appeared at **every boot** from the earliest capture
until the fix, then stopped. Evidence lives in **rsyslog archives** — journald
was configured with `MaxRetentionSec=14day` (Phase 8), so Aug kernel logs were
pruned. Source: `/var/log/kern.log.4.gz` (Aug 23–30), `.3.gz` (Aug 30–Sep 6),
`.2.gz` (Sep 6–13).

| Boot | BERT fatal `P0H0` | Kernel `Memory:` total | e820 `remove [mem 0x28090000000-…]` |
|------|-------------------|------------------------|--------------------------------------|
| 2026-08-24 03:04 | ✗ fatal | 98,680,396 K (~94.1 GiB) | ✗ present |
| 2026-08-26 09:29 | ✗ fatal | 98,685,132 K | ✗ present |
| 2026-09-07 03:04 | ✗ fatal | 98,679,912 K | ✗ present |
| 2026-09-10 05:49 | ✗ fatal | 98,678,240 K | ✗ present |
| 2026-10-11 12:42 → 14:33 | ✗ fatal | ~98,675,000 K | ✗ present |
| **2026-10-11 15:37 → now** | **✓ gone** | **114,139,852 K (~108.9 GiB)** | **✓ gone** |

Every pre-fix boot excluded the channel-H range from e820; the `Memory:` total
grew by exactly **15.46 GB** ≈ one 16 GB DIMM on the first post-fix boot. The
machine ran on **7 channels for ~7 weeks** before the standoff was removed.
Current BERT table: 48 bytes = header only (no record). EDAC `mc0 ce/ue = 0/0`.

**Journald caveat:** `MaxRetentionSec=14day` means journald alone won't hold
older boots — always check `/var/log/kern.log*.gz` (rsyslog) for pre-two-week
evidence.

---

## Post-fix validation (2026-10-11)

### Memory stress test — all 8 sticks

```bash
stress-ng --vm 8 --vm-bytes 10G --vm-method all --timeout 240s --metrics-brief
```

```text
stress-ng: metrc: vm  58475455  240.45  1539.35  369.08  243191.83  30640.51
stress-ng: info:  passed: 8: vm (8)
stress-ng: info:  failed: 0
```

Result: **PASSED** — 8/8 workers, 0 failures, 0 crashes.

### Memory bandwidth benchmark

The developer CPU quota (Phase 9) caps the owner slice at 8 cores, which
throttles a memory benchmark to a meaningless ~6 GiB/s. Run **outside** the
user slice:

```bash
# build
gcc -O3 -fopenmp -march=native scripts/stress/stream-bench.c -o /tmp/stream-bench -lm

# run with all 128 threads, outside the user slice
sudo systemd-run --scope --slice=system -p CPUQuota=12800% \
  env OMP_NUM_THREADS=128 OMP_PROC_BIND=spread /tmp/stream-bench 4096
```

```text
Copy  :   68660.5 MiB/s  (  67.1 GiB/s)
Scale :   68235.5 MiB/s  (  66.6 GiB/s)
Add   :   76065.0 MiB/s  (  74.3 GiB/s)
Triad :   77085.4 MiB/s  (  75.3 GiB/s)
RandR :    7733.6 MiB/s  (   7.6 GiB/s)
RandW :    5244.6 MiB/s  (   5.1 GiB/s)
RandRW:    5449.4 MiB/s  (   5.3 GiB/s)
```

Measured on the **full 8-channel** configuration: **~75 GiB/s streaming Triad**,
**~7.6 GiB/s random read**. Full analysis in
`docs/guides/operations/system-test-results.md` §3b.

### Final health check

```bash
cat /sys/devices/system/edac/mc/mc0/{ce_count,ue_count}   # 0 / 0
free -h                                                   # 123Gi total
```

No ECC errors after the stress + bandwidth suite; governor restored to
`schedutil`.
