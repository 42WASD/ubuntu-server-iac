# platform groups

Create:

```bash
sudo groupadd -f ssh-users
sudo groupadd -f tenant-jya0
sudo groupadd -f tenant-42admin
sudo groupadd -f gpu-approved
```

Owner:

```bash
sudo usermod -aG sudo,ssh-users jyao
```

Developer:

```bash
sudo usermod -aG ssh-users,tenant-jya0 jya0
```

Future 42 contributor:

```bash
sudo adduser alice
sudo usermod -aG ssh-users,tenant-42admin alice
```

Do not add normal developers to:

```text
sudo
docker
lxd
libvirt
disk
root
```

Those groups may grant more authority than their names suggest.

---
