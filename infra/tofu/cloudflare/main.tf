# Cloudflare tunnel credential — Part XVII, Phase 67/68.
#
# Stores the cloudflared tunnel token (currently a k8s Secret in the ingress
# namespace) so it is captured in encrypted remote state (Cloudflare R2 via
# the S3 backend) as a reproducible, backed-up source of truth.
#
# The token value comes from the gitignored `terraform.tfvars` (or env) —
# never committed.
terraform {
  backend "s3" {
    bucket = "42base"
    key    = "cloudflare/terraform.tfstate"
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

resource "terraform_data" "cloudflared_tunnel" {
  input = {
    tunnel_token = var.cloudflared_tunnel_token
  }
}