# SSH hardening

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

## Status on `alpha` (2026-08-29): NOT applied — deferred

The baseline above is **recommendation, not current state**. This phase is
tracked as `deferred` in `docs/implementation/progress.yaml`. Live sshd on
`alpha` is still the stock Ubuntu configuration:

```bash
sudo sshd -T | grep -iE '^passwordauthentication|^permitrootlogin'
# passwordauthentication yes
# permitrootlogin prohibit-password
```

Mitigations currently in place instead: the host firewall
(`platform-nftables.service`) restricts inbound SSH, and developer access
flows through named accounts + groups (Phase 4). Apply this drop-in when the
phase is picked up — it documents the intended end state.
