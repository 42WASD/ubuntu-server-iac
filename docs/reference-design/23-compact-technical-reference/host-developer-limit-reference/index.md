---
order: 3
---

# Host developer-limit reference

Normal developer:

```text
CPUQuota=400%
MemoryHigh=8G
MemoryMax=12G
TasksMax=4096
IOWeight=50
home hard quota ~40-50 GB
```

Heavy trusted developer (`jya0` style):

```text
CPUQuota=800%
MemoryHigh=16G
MemoryMax=24G
TasksMax=8192
IOWeight=75
home hard quota ~150-200 GB
```

Tune from measurements.

---
