# Phase 18 — verify reboot recovery now, not later

Before installing ten add-ons:

```bash
sudo reboot
```

After reconnecting:

```bash
systemctl is-active rke2-server
kubectl get nodes
kubectl get pods -A
```

Wait for reconciliation.

Record boot time:

```bash
systemd-analyze
systemd-analyze blame | head -30
```

## Checkpoint 11

A normal reboot should require:

```text
zero manual "docker start"
zero manual "kubectl apply"
zero manual CNI repair
```

If it does, fix that now.

---
