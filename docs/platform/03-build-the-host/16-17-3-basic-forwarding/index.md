# basic forwarding

Create:

```bash
sudoedit /etc/sysctl.d/99-platform-network.conf
```

Use:

```sysctl
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
```

Apply:

```bash
sudo sysctl --system
```

---
