# Variables for the two external VPS connection details.
# Values are supplied from the gitignored `terraform.tfvars` (or env).

variable "hostzealot_plan" {
  description = "Hostzealot VPS plan"
  type        = string
  default     = "KVM-SSD 2048"
}

variable "hostzealot_hostname" {
  description = "Hostzealot VPS hostname"
  type        = string
  default     = "srv147014.yourbestnetwork.net"
}

variable "hostzealot_public_ip" {
  description = "Hostzealot VPS public IP"
  type        = string
  default     = "89.44.80.176"
}

variable "hostzealot_ssh_user" {
  description = "Hostzealot VPS SSH user"
  type        = string
  default     = "root"
}

variable "hostzealot_ssh_port" {
  description = "HostZealot VPS SSH port"
  type        = number
  default     = 56777
}

variable "hostzealot_ssh_password" {
  description = "HostZealot VPS SSH password (SECRET)"
  type        = string
  sensitive   = true
}

variable "melbicom_plan" {
  description = "Melbicom VPS plan"
  type        = string
  default     = "KVM-2-FJR"
}

variable "melbicom_hostname" {
  description = "Melbicom VPS hostname"
  type        = string
  default     = "263347.melbi.space"
}

variable "melbicom_public_ip" {
  description = "Melbicom VPS public IP (UAE/Fujairah relay)"
  type        = string
  default     = "89.36.162.171"
}

variable "melbicom_ssh_user" {
  description = "Melbicom VPS SSH user"
  type        = string
  default     = "root"
}

variable "melbicom_ssh_password" {
  description = "Melbicom VPS SSH password (SECRET)"
  type        = string
  sensitive   = true
}