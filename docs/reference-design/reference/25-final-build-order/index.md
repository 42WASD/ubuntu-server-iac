# Part XXV — Final build order

For this exact platform, do it in this order:

```text
01  Git infrastructure repository
02  host inventory / disk verification
03  Ubuntu update + base packages
04  users/groups/sudo
05  SSH hardening
06  Tailscale
07  host nftables
08  sysctl/journald
09  developer cgroup + disk quotas
10  storage/LVM
11  NVIDIA host driver only
12  pinned RKE2
13  bundled Cilium config
14  Traefik
15  reboot validation
16  Argo CD bootstrap
17  namespaces/RBAC/quota/LimitRange
18  Pod Security + NetworkPolicy
19  Kyverno audit
20  OpenEBS LocalPV LVM
21  PVC tests
22  monitoring/logging
23  Harbor
24  build01 + remote BuildKit
25  Skaffold developer loop
26  CI pipeline
27  Cloudflare
28  external status
29  UAE WireGuard relay
30  game platform
31  whole-GPU Kubernetes test
32  GPU policy
33  HAMi experiment
34  offsite backups
35  Ansible conversion
36  Autoinstall validation
37  OpenTofu external resources
38  full disaster-recovery test
39  add future RKE2 workers
```

The rule throughout is:

```text
PROVE
    -> AUTOMATE
        -> VERSION
            -> MONITOR
                -> BACK UP
                    -> ONLY THEN EXPAND
```

That is the difference between a pile of installed software and a platform you can trust, reproduce, and grow.
