# Host `beta` — NVIDIA GPU Driver (nouveau) & Hardware Status

This guide covers the GPU driver setup and the hardware status of the two
NVIDIA GPUs on the secondary server **`beta`** (`192.168.8.135`).

## Hardware

| GPU | Bus | Architecture | Status |
|-----|-----|--------------|--------|
| NVIDIA GeForce GTX 1070 | `0000:07:00.0` | Pascal (GP104) | ✅ **Working (nouveau)** |
| NVIDIA GeForce RTX 3070 Mobile / Max-Q | `0000:06:00.0` | Ampere (GA104M) | ❌ fails to init (isolated) |

## Driver Selection History

Several proprietary driver attempts were made before settling on the open-source
**nouveau** driver.

### 1. Proprietary `595-server` (595.71.05) — dropped Pascal

The 595 branch **dropped Pascal support**, so the GTX 1070 was ignored at boot:

```
NVRM: ignoring the legacy GPU 0000:07:00.0
```

The RTX 3070 Mobile also failed under 595 with `RmInitAdapter failed`.

### 2. Proprietary `580-server` and "FrankenDriver" (580.173 / 580.142)

The 580 branch supports both Pascal and Ampere. It drove the **GTX 1070 at 75W**
(with CUDA and `nvidia-smi`), but the **RTX 3070 Mobile still failed** under
every GSP-firmware configuration. A community "FrankenDriver" (580.142) was
also tested: it bound the 3070 but could not fully initialize it.

### 3. Open-source `nouveau` (current)

The proprietary drivers were removed and the open-source **nouveau** driver was
enabled. This is the current, working configuration.

## Why the RTX 3070 must be isolated

Under **nouveau**, the broken RTX 3070 Mobile does **not** fail gracefully — it
triggers a **kernel NULL-pointer dereference (oops)** during probe:

```text
nouveau 0000:06:00.0: NVIDIA GA104 (b74000a1)
nouveau 0000:06:00.0: gsp: RM version: 570.144
nouveau 0000:06:00.0: bios: version 94.04.35.00.25
nouveau 0000:06:00.0: preinit failed with -110
BUG: kernel NULL pointer dereference, address: 000000000000001c
RIP: 0010:iommu_dma_unmap_sg+0xd/0x170
 Call Trace:
  nvkm_gsp_sg_free+0x25/0x90 [nouveau]
  r535_gsp_dtor+0x2b/0x150 [nouveau]
```

The GSP firmware times out (`preinit failed with -110` = `ETIMEDOUT`) because of
the invalid vBIOS, and nouveau's GSP teardown path dereferences a NULL pointer.
If the card is left bound at boot, it can **hang the boot**. It must therefore be
prevented from binding **any** driver.

### udev rule — isolate the RTX 3070

Create `/etc/udev/rules.d/80-nvidia-3070-nobind.rules` (device `10de:249d`):

```text
# Prevent any driver from binding the broken RTX 3070 Mobile (GA104, 10de:249d)
# at 06:00.0. Its blank vBIOS causes a GSP preinit timeout (-110) and a kernel
# oops (iommu_dma_unmap_sg) during nouveau init. "none" is a non-existent driver
# so no driver can match/bind this device.
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{device}=="0x249d", ATTR{driver_override}="none"
```

> ⚠️ **Important:** after writing this rule you must **reboot** — do not try to
> apply it live. Unbinding a device that nouveau already crashed on returns
> `Permission denied`. The rule only works at boot (device-add) time, before
> nouveau binds. If boot hangs before the rule takes effect, power-cycle and the
> rule will apply on the next boot.

### Verify

```bash
# 3070 must show override=none and NO driver bound
cat /sys/bus/pci/devices/0000:06:00.0/driver_override   # -> none
readlink /sys/bus/pci/devices/0000:06:00.0/driver       # -> (empty, no driver)

# GTX 1070 must be bound to nouveau and expose a DRM device
readlink /sys/bus/pci/devices/0000:07:00.0/driver       # -> .../nouveau
ls /dev/dri/                                            # -> by-path  card0  renderD128
cat /sys/class/drm/card0/device/uevent                  # PCI_ID=10DE:1B81 (GTX 1070)
```

## Trade-off — no power limiting under nouveau

nouveau provides **no `nvidia-smi`**, **no CUDA**, and **no power limiting**
(`nvidia-smi -pl` is unavailable). On `beta`, the GTX 1070 therefore runs at its
**default power** with no way to cap it. The previous 75W power-limit service
(`scripts/gpu/beta-nvidia-power-limit.service`) no longer applies and has been
removed from the host. This was accepted in favor of a stable, fully open-source
driver.

## RTX 3070 Mobile — root cause

The `GA104M` (RTX 3070 Mobile / Max-Q) is a mobile chip mounted on a desktop
adapter ("frankenstein" build). It fails to initialize under **every** driver:

- **Proprietary driver** reads a blank vBIOS: `Video BIOS: ??.??.??.??.??`
- **nouveau** reads the real BIOS but its GSP firmware **times out** (`-110`) and
  the driver then oopses.
- The subsystem ID is blank/zero, a hallmark of a missing/mismatched vBIOS.

Because the card never comes up, it **cannot be queried or power-limited**, and
under nouveau it **must be isolated** (see above) to keep the host stable.

### Possible fixes (hardware/firmware level, not pursued)

1. **vBIOS flash** — flash a matching mobile RTX 3070 vBIOS (risky; typically via
   a Windows tool or `nvflash`).
2. **BIOS settings** — confirm `Above 4G Decoding` and **Resizable BAR**.
3. **Power delivery** — verify the auxiliary 6/8-pin is seated.
4. **Seat / reseat** — reinsert the card and confirm the slot link.

Until resolved, **only the GTX 1070** is usable on `beta`, driven by `nouveau`
with no CUDA and no power-limiting.