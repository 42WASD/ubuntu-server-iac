# no shared human account

If an account named `42admin` exists as a service/project account, prevent interactive shell access:

```bash
sudo usermod -s /usr/sbin/nologin 42admin
```

Human developers use:

```text
alice
bob
carol
```

not:

```text
everyone -> 42admin
```

---
