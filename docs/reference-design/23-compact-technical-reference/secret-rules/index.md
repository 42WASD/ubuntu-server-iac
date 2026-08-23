# Secret rules

Never commit:

```text
RKE2 token
Tailscale auth key
Cloudflare tunnel token
Cloudflare API token
Harbor admin password
registry robot secret
WireGuard private key
OpenTofu state with secrets
Ansible Vault password
private SSH key
kubeconfig with admin client certificate
```

Commit:

```text
templates
encrypted secret objects
secret names
policy
documentation
public keys when appropriate
```

---
