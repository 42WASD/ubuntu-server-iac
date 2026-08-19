# sudo policy

Keep normal `/etc/sudoers` minimal.

Use:

```bash
sudo visudo -f /etc/sudoers.d/platform-admin
```

Example:

```sudoers
jyao ALL=(ALL:ALL) ALL
```

Do **not** give tenant users convenience rules such as:

```sudoers
alice ALL=(ALL) NOPASSWD: ALL
```

That negates nearly every other isolation control.

## Checkpoint 3

As a normal developer:

```bash
sudo -l
```

Expected:

```text
not allowed to run sudo
```

As `jyao`:

```bash
sudo -v
```

Expected:

```text
works
```

---
