# Current verification caveats — read before installing

## 7.1 Ubuntu 26.04 + RKE2

Current RKE2 documentation says RKE2 should generally work on Linux distributions using systemd and iptables, while the separate SUSE support matrix defines combinations formally validated by the vendor.

This guide therefore treats Ubuntu 26.04 as:

```text
reasonable technical target
+
must pass our validation gates
+
do not assume vendor support matrix coverage merely because installation succeeds
```

## 7.2 RKE2 v1.36 ingress

The old community `ingress-nginx` Kubernetes controller reached end-of-life in March 2026.

For new RKE2 v1.36 clusters, Traefik is the default direction.

This guide explicitly selects:

```yaml
ingress-controller: traefik
```

## 7.3 GPU Operator + Ubuntu 26.04

NVIDIA's current GPU Operator platform-support matrix lists Ubuntu 22.04 and 24.04 for the validated RKE2 combinations; Ubuntu 26.04 is not currently listed in that matrix.

Therefore:

```text
DO NOT make GPU Operator a prerequisite for the base cluster.
```

First prove:

```text
Ubuntu NVIDIA driver
-> nvidia-smi
-> stable reboot
-> stable RKE2
```

Then evaluate the GPU integration separately.

## 7.4 HAMi

HAMi is an optional later layer.

Do not let:

```text
HAMi experiment fails
```

become:

```text
entire Kubernetes platform cannot boot
```

Whole-GPU scheduling comes first.

## 7.5 Local storage

OpenEBS LocalPV LVM is **local** storage.

If `alpha` dies, those volumes are unavailable until `alpha` is restored.

LocalPV provides:

```text
dynamic provisioning
filesystem/LVM management
Kubernetes PVC lifecycle
```

It does not create a second physical copy of your data on another server.

Backups are separate.

---
