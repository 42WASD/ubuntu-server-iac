---
phase: 17-opentofu-for-external-infrastructure/what-opentofu-should-own
---

# Phase 67 — what OpenTofu should own

Set up OpenTofu to own/store the *connection details* of the external
components this platform depends on (the two VPSes + the Cloudflare tunnel
credential), per Phase 67: OpenTofu is responsible for resources created
through external APIs and their connection data. Ansible remains responsible
for host configuration (apt packages, `sshd_config`, RKE2 systemd), which is
out of OpenTofu's scope.

## 67.1 What was set up

`infra/tofu/` — two OpenTofu modules, each backed by the same R2 bucket `42base`:

- `infra/tofu/vps/` — stores connection details for the two external VPSes
  (hostzealot + melbicom) via built-in `terraform_data` resources. No external
  provider exists for these VPSes, so nothing is provisioned; OpenTofu only
  tracks the *credentials* in encrypted remote state.
- `infra/tofu/cloudflare/` — stores the `cloudflared` tunnel token via
  `terraform_data`, capturing the credential that is currently a Kubernetes
  Secret.

Key files:

- `infra/tofu/vps/main.tf`, `variables.tf`, `terraform.tfvars.example`
- `infra/tofu/cloudflare/main.tf`, `variables.tf`, `terraform.tfvars.example`
- `infra/tofu/.gitignore` — ignores `*.tfstate`, `*.tfstate.*`, `.terraform/`,
  `crash.log`, `terraform.tfvars`; re-includes `!terraform.tfvars.example`.

Secret values are read from the gitignored `terraform.tfvars` (or env), never
from committed code.

## 67.2 Backend: Cloudflare R2 via the S3 backend

OpenTofu's stable release has no ORAS/GHCR backend, so Cloudflare R2 was chosen
as an S3-compatible remote state backend. Bucket `42base` holds the state keys.

Backend block (both modules, different `key`):

```hcl
terraform {
  backend "s3" {
    bucket = "42base"
    key    = "vps/terraform.tfstate"        # or "cloudflare/terraform.tfstate"
    region = "auto"
    endpoint = "https://70e06cd0a78575fb48251884ac37f859.r2.cloudflarestorage.com"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}
```

The `skip_*` options and `use_path_style = true` are required because R2 is
S3-compatible but not AWS. Credentials are supplied via the standard
`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars (region `auto`).

## 67.3 Commands run

Create the R2 bucket `42base` (via the Cloudflare API; `opentofu-state` was
created first, then deleted and replaced by `42base`):

```bash
# create bucket
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/<ACCT>/r2/buckets/42base" \
  -H "Authorization: Bearer <API_TOKEN>"

# delete the superseded bucket
curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/<ACCT>/r2/buckets/opentofu-state" \
  -H "Authorization: Bearer <API_TOKEN>"
```

Configure S3 credentials for the backend and initialize the VPS module:

```bash
export AWS_ACCESS_KEY_ID=<ACCESS_KEY_ID>
export AWS_SECRET_ACCESS_KEY=<SECRET_ACCESS_KEY>
export AWS_REGION=auto
export AWS_DEFAULT_REGION=auto

cd infra/tofu/vps
tofu init -input=false
tofu plan -input=false -no-color
tofu apply -input=false -auto-approve -no-color
```

Verify the two VPS connection records were planned and applied:

```bash
cd infra/tofu/vps
tofu plan -input=false -no-color
```

The plan shows `+ resource "terraform_data" "hostzealot"` and
`terraform_data "melbicom"` being created with their connection details
(`public_ip`, `ssh_user`, `ssh_port`, `ssh_password` — the password shows as a
sensitive value). Result: `Plan: 2 to add, 0 to change, 0 to destroy`, then
`Apply complete! Resources: 2 added`.

Repeat for the cloudflare module:

```bash
cd ../cloudflare
tofu init -input=false
tofu apply -input=false -auto-approve -no-color
```

Result: `Plan: 1 to add`, `Apply complete! Resources: 1 added`.

## 67.4 What was verified

- `tofu init` on `infra/tofu/vps` configured the R2 S3 backend successfully.
- `tofu plan` showed exactly the two VPS `terraform_data` resources.
- `tofu apply` created both, `Apply complete! Resources: 2 added`.
- `tofu apply` on `infra/tofu/cloudflare` created the tunnel-token resource,
  `Apply complete! Resources: 1 added`.
- State objects are present in R2 bucket `42base`:

```text
cloudflare/terraform.tfstate   1037 bytes
vps/terraform.tfstate          2201 bytes
```

(confirmed via an S3 `list_objects_v2` against the R2 endpoint).

## 67.5 Troubleshooting

- **403 `SignatureDoesNotMatch` during `tofu init`**: the access key ID / secret
  access key pair did not match. The bucket and endpoint were correct; the
  fault was the key pair. Fix: create a fresh R2 S3 API token in the Cloudflare
  dashboard and use its exact Access Key ID + Secret Access Key. (Also catch a
  typo in the secret — a single mistyped hex digit reproduces this error.)
- The custom domain endpoint (`s3.42base.com`) was NOT mapped to the bucket and
  returned 404 on `ListObjectsV2`; the default account endpoint
  `<ACCOUNT_ID>.r2.cloudflarestorage.com` is the correct one to use.

## 67.6 Infra encoding

- OpenTofu modules + R2 backend live in `infra/tofu/`.
- `.gitignore` protects `terraform.tfvars` (secrets) and all state files;
  `terraform.tfvars.example` is committed as documentation.
- These connection details are now reproducible + backed up in encrypted remote
  state and never need to be pasted ad hoc.