---
order: 5
---

# Phase 5 — SSH hardening

Create a drop-in:

```bash
sudoedit /etc/ssh/sshd_config.d/50-platform.conf
```

Recommended baseline:

```text
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes

AllowGroups ssh-users

X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding yes

ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 4
LoginGraceTime 30
```

Why keep TCP forwarding?

Because developers may legitimately use:

```text
kubectl port-forward
SSH local forwards
remote development tooling
```

Do not disable useful developer functionality unless you have a threat reason.

Validate **before restarting**:

```bash
sudo sshd -t
```

If there is no output:

```bash
sudo systemctl reload ssh
```

Keep your current SSH session open and test a second session before logging out.

## Checkpoint 4

From another machine:

```bash
ssh <user>@<current-alpha-ip>
```

Then test password authentication is rejected.

---
