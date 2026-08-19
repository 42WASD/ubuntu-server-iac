# Phase 66 — validate Autoinstall in a VM first

Before using on `alpha`:

```text
create VM
attach two fake disks matching the intended size pattern
boot Ubuntu installer
feed autoinstall
verify the correct disk was destroyed
verify resulting LVM layout
verify SSH key access
```

Then use the generated installer data as another reference.

Ubuntu also writes an autoinstall representation from an installation under:

```text
/var/log/installer/autoinstall-user-data
```

Use that as a starting point, sanitize secrets, then commit your edited template.

---
