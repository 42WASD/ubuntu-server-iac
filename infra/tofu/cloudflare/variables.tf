# Variables for the Cloudflare tunnel credential.

variable "cloudflared_tunnel_token" {
  description = "cloudflared tunnel token (SECRET, from k8s secret cloudflared-token)"
  type        = string
  sensitive   = true
}