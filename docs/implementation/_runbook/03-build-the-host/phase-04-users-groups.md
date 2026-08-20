---
phase: 03-build-the-host/05-13-phase-4-users-groups-and-sudo-boundaries
---
# Phase 4 — users, groups, and sudo boundaries

**Intent:** platform tenant groups, existing-account membership, minimal sudo —
**no new shared human account**.

## 4.1 Platform groups + `jyao`

```bash
# Create platform groups
for g in ssh-users tenant-jya0 tenant-42wasd-admin gpu-approved; do
  sudo groupadd -f "$g"
done

# Owner membership
sudo usermod -aG sudo,ssh-users jyao
```

Verified: `ssh-users` → `jyao`, `jyao-42admin`; `tenant-42wasd-admin` →
`jyao-42admin`; `jyao` in `sudo`.

## 4.2 Add the 42wasd-admin tenant user

```bash
sudo useradd -m -s /bin/bash -G ssh-users,tenant-42wasd-admin \
  -c "jyao 42admin tenant" jyao-42admin
echo 'jyao-42admin:jyao' | sudo chpasswd
```

Verified: `jyao-42admin` UID 1001, groups `jyao-42admin ssh-users
tenant-42wasd-admin`.

## 4.3 Sudo policy (minimal)

Kept `/etc/sudoers` untouched. `jyao` retains `(ALL:ALL) ALL`; no convenience
`NOPASSWD` rules for tenants.

**Checkpoint 3 (verified):**
- As a normal developer: `sudo -l` → not allowed.
- As `jyao`: `sudo -v` → works.

## Group rename (post hoc)

```bash
sudo groupmod -n tenant-42wasd-admin tenant-42admin
```
Renamed for clarity/consistency; reflected in infra + docs.

**Infra encoding:** `infra/ansible/roles/users/` — `defaults` (groups +
membership), `tasks`, `templates/platform-admin.j2`.