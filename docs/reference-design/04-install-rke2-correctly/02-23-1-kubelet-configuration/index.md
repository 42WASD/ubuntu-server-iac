# kubelet configuration

RKE2's current preferred pattern is to use kubelet config drop-ins rather than piling everything into CLI flags.

We want two effects:

```text
1. reserve capacity for Linux + developers + Kubernetes system services
2. protect the host from disk/memory exhaustion
```

Create the directory after RKE2 installs, or pre-create the RKE2-supported config location as part of automation.

Recommended initial target:

```text
physical:
  64 CPU
  128 GiB

leave outside normal Pod scheduling:
  roughly 12 CPU
  roughly 24 GiB

Kubernetes system reservation:
  roughly 2 CPU
  roughly 4 GiB
```

This leaves a large workload budget while admitting that SSH users and the host exist outside Pod scheduling.

Do **not** attempt to schedule 128 GiB of Pod requests on a machine where developers also compile and test software directly.

Example kubelet configuration fields to evaluate/pin in your Ansible role:

```yaml
systemReserved:
  cpu: "12"
  memory: "24Gi"
  ephemeral-storage: "20Gi"

kubeReserved:
  cpu: "2"
  memory: "4Gi"
  ephemeral-storage: "10Gi"

evictionHard:
  memory.available: "8Gi"
  nodefs.available: "12%"
  imagefs.available: "15%"
  nodefs.inodesFree: "5%"

imageGCHighThresholdPercent: 75
imageGCLowThresholdPercent: 60

seccompDefault: true
```

**Do not blindly assume the exact kubelet config schema for your pinned Kubernetes minor.** Keep this as a versioned file, validate it against the version you installed, and inspect kubelet logs after first boot.

---
