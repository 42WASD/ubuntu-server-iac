# VPS connection details — Part XVII, Phase 67/68 (OpenTofu for external infra).
#
# These resources do NOT provision anything (no VPS provider exists for
# hostzealot / melbicom). They exist so OpenTofu tracks the *connection
# details* of the two external VPSes in encrypted remote state (Cloudflare R2
# via the S3 backend), so the values are reproducible + backed up and never
# need to be pasted ad hoc.
#
# Actual secret values come from the gitignored `terraform.tfvars` (or env),
# never from committed code.
terraform {
  backend "s3" {
    bucket = "42base"
    key    = "vps/terraform.tfstate"
    region = "auto"

    endpoint = "https://70e06cd0a78575fb48251884ac37f859.r2.cloudflarestorage.com"

    # R2 is S3-compatible but not AWS; skip AWS-specific validation/checks.
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}

# terraform_data is a built-in resource (no external provider) that stores an
# arbitrary value in state. We use it to persist each VPS's connection details
# so they land in the encrypted remote state.
resource "terraform_data" "hostzealot" {
  input = {
    provider       = "hostzealot"
    plan           = var.hostzealot_plan
    hostname       = var.hostzealot_hostname
    public_ip      = var.hostzealot_public_ip
    ssh_user       = var.hostzealot_ssh_user
    ssh_port       = var.hostzealot_ssh_port
    ssh_password   = var.hostzealot_ssh_password
  }
}

resource "terraform_data" "melbicom" {
  input = {
    provider       = "melbicom"
    plan           = var.melbicom_plan
    hostname       = var.melbicom_hostname
    public_ip      = var.melbicom_public_ip
    ssh_user       = var.melbicom_ssh_user
    ssh_password   = var.melbicom_ssh_password
  }
}