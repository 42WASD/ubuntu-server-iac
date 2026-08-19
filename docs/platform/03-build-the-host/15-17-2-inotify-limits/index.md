# inotify limits

RKE2 documentation specifically calls out higher inotify requirements for workloads that create many watchers.

Create:

```bash
sudoedit /etc/sysctl.d/99-platform-inotify.conf
```

Use:

```sysctl
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
```

Apply:

```bash
sudo sysctl --system
```

Verify:

```bash
sysctl fs.inotify.max_user_instances
sysctl fs.inotify.max_user_watches
```

---
