variable "name" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "subnet_id" { type = string }
variable "admin_username" {
  type    = string
  default = "azureuser"
}
variable "ssh_public_key" { type = string }
variable "allowed_ssh_cidr" {
  type        = string
  description = "Your public IP as CIDR, e.g. 203.0.113.7/32. Never use 0.0.0.0/0."
  validation {
    condition     = var.allowed_ssh_cidr != "0.0.0.0/0" && can(cidrhost(var.allowed_ssh_cidr, 0))
    error_message = "Provide a specific CIDR (not 0.0.0.0/0)."
  }
}
variable "tags" {
  type    = map(string)
  default = {}
}
