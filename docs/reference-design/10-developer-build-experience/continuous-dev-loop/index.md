# continuous dev loop

Target command:

```bash
skaffold dev
```

Desired behavior:

```text
save source
-> detect change
-> file-sync when possible
OR
-> remote build
-> run tests
-> push dev image
-> deploy dev manifest
-> tail logs
```

For interpreted languages, use file sync where practical.

Example:

```text
Python source changed
    -> sync / reload

requirements.lock changed
    -> full image rebuild
```

This keeps the loop fast while preserving a production-like container image path.

---
