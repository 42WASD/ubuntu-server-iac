# keep game workloads in Kubernetes for now

Do not solve individual game stacks yet.

Platform-level decision:

```text
dev-games-42wasd-admin
prd-games-42wasd-admin
```

gets:

```text
ResourceQuota
LimitRange
NetworkPolicy
persistent storage
monitoring
controlled external ports
```

That keeps game hosting inside the same infrastructure discipline.

Later we can choose per game:

```text
plain StatefulSet
Agones
operator
proxy layer
specialized controller
```

without changing the host platform.

## Game staging lane — deep-copy on demand

`prd-games-42wasd-admin` is the canonical production lane. There is **no
permanent** dev environment for games. Instead, `dev-games-42wasd-admin` is an
**ephemeral, on-demand staging lane** used one game server at a time.

Method:

```text
1. pick ONE game server (e.g. CS2 or Minecraft) in prd-games-42wasd-admin
2. deep-copy it 1:1 into dev-games-42wasd-admin
   - snapshot the game world's PersistentVolume (VolumeSnapshot)
   - restore the snapshot as a new PVC in dev-games-42wasd-admin
   - copy configs/secrets, not just the app manifest, so the test is faithful
3. run the upgrade / test / ops in the staging lane
4. once the solution is confirmed, promote it back to prd-games-42wasd-admin
5. delete the staging copy in dev-games-42wasd-admin (it is throwaway)
```

`dev-games-42wasd-admin` is intentionally lightweight: it holds at most one
copied game server at a time, is **not** a source of truth, and is excluded from
backups-as-canonical. Upgrades are serialized one game at a time so a bad
upgrade only ever touches the disposable copy.

---
