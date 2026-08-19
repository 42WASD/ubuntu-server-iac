# Phase 50 — first GPU goal: whole-GPU scheduling

Goal:

```text
Pod asks for:
  nvidia.com/gpu: 1

scheduler sees:
  2 allocatable GPUs

Pod runs nvidia-smi/CUDA sample successfully
```

Do not install HAMi until that works.

RKE2 has GPU Operator integration guidance that accounts for its embedded containerd path.

Do **not** blindly run generic `nvidia-ctk runtime configure --runtime=containerd` against a system containerd path and assume it modified RKE2's embedded containerd.

Follow the pinned RKE2 GPU integration documentation for the RKE2 version you are actually running.

---
