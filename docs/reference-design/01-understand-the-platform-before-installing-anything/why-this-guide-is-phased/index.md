---
order: 10
---

# Why this guide is phased

The most dangerous infrastructure mistake is installing ten moving parts before proving the first two work.

The build order is therefore:

```text
1. prove host
2. prove management access
3. prove storage
4. prove Kubernetes
5. prove cluster networking
6. prove GitOps
7. prove policy
8. prove persistent storage
9. prove application deployment
10. prove monitoring
11. prove registry/build flow
12. prove public web exposure
13. prove GPU separately
14. add game networking
15. automate reinstall/rebuild
```

Each phase has a **checkpoint**.

If a checkpoint fails, do not continue.

---
