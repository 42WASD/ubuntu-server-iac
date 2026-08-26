# swap: disable for bring-up, then re-enable as a host safety net

## Phase 1 — disable for the initial cluster bring-up

Check:

```bash
swapon --show
```

If swap exists, disable for the initial Kubernetes deployment:

```bash
sudo swapoff -a
```

Comment the swap entry in `/etc/fstab` if you intend to keep it disabled.

Why start this way?

```text
predictable memory accounting
fewer variables during first cluster validation
```

## Phase 2 — re-enable once the cluster is validated (deliberate feature)

The disable above is **temporary** — it exists to reduce variables while the
cluster is first validated. Kubernetes pods have their **own cgroup memory
limits** and are **not** protected/limited by host swap, so re-enabling host
swap does NOT change pod accounting.

After the cluster is stable, **re-enable swap as a host-level safety net**.
Rationale (observed 2026-08-26):

- A heavy interactive build (`dotnet publish -m:16` writing WASM AOT to the
  **RAM-backed** `/tmp` tmpfs) ran with **swap disabled (zero headroom)** and
  hard-froze the whole host (kernel log stopped with no panic/OOM). A swap
  pressure absorber would have let the kernel make progress instead of
  hard-locking.
- Pod memory is unaffected — the swap is for interactive host workloads
  (builds, `make -j`, pytest, etc.), not for pods.

```bash
# confirm the swap file is still valid
ls -lh /swap.img                            # 8.0G Linux swap file

# persist it across reboots
echo '/swap.img none swap sw 0 0' >> /etc/fstab

# activate now
sudo swapon /swap.img
```

Verify:

```bash
swapon --show                                # /swap.img file 8G 0B -1
systemctl list-units --type=swap --all       # swap.img.swap loaded active
free -h | grep -i swap                       # Swap: 8.0Gi 0B
```

**Corollary — users and `/tmp`:** on this host `/tmp` is a **RAM-backed
tmpfs** (`size=50%`), so writing there consumes system RAM, not disk. Small
transient files are fine; **large build/publish outputs belong on real disk**
(`/var/tmp/`, `~/publish`, a workspace), not `/tmp`.

---
