---
phase: 04-install-rke2-correctly/04-25-phase-16-install-and-start-rke2/verify-rke2-secrets-encryption
---
# Phase 25.2 — verify RKE2 Secrets encryption

**Intent:** confirm Secrets-at-rest encryption is enabled for the running
cluster via RKE2's `secrets-encrypt` administration command.

## 25.2.1 Status check

```bash
sudo rke2 secrets-encrypt status
```

Observed:

```text
Encryption Status: Enabled
Current Rotation Stage: start
Server Encryption Hashes: All hashes match

Active  Key Type  Name
------  --------  ----
 *      AES-CBC   aescbckey
```

✅ `Encryption Status: Enabled` — Secrets are encrypted at rest with a single
`AES-CBC` key (`aescbckey`), and all server encryption hashes match.

## 25.2.2 Key rotation

Per the reference design, we do **not** rotate keys during initial bootstrap.
Key rotation is a separate maintenance procedure and must be preceded by an
etcd snapshot (see the etcd snapshot schedule configured in Phase 14).

## 25.2.3 Result

Secrets-at-rest encryption is confirmed **Enabled**. No rotation performed.