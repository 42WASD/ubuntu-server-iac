# What each developer is allowed to do

A normal developer should be able to:

```text
SSH through Tailscale
clone Git repositories
edit source code
create Python venvs
install packages inside venvs
install project-local npm/pnpm dependencies
run unit tests
run compilers
use kubectl in authorized namespaces
view logs
exec into dev Pods
port-forward dev services
run skaffold dev
request a remote container build
push approved images to their registry project
promote their own application through GitOps
```

A normal developer should **not** be able to:

```text
sudo
become root
use cluster-admin
mount arbitrary hostPath
create privileged Pods
use hostNetwork/hostPID/hostIPC
control the host container runtime
mount /var/run/docker.sock
alter CNI / CSI / admission webhooks
change cluster-wide RBAC
request GPUs unless approved
consume unlimited CPU/RAM/disk/PIDs
read other tenants' Secrets
```

---
