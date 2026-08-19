# Phase 55 — relay bring-up

Start with one relay candidate.

Recommended experimental order:

```text
1. OCI UAE Always Free if capacity/account conditions allow
2. low-cost Dubai VPS
3. paid OCI/AWS/Azure UAE if reliability requirements justify it
```

Do not permanently choose on provider marketing.

Benchmark:

```bash
ping
mtr
iperf3
iperf3 -u
```

Measure:

```text
median latency
p95
p99
jitter
packet loss
evening peak behavior
real UAE mobile path
GCC path if relevant
```

---
