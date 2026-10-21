variable "subscription_id" { type = string }
variable "project" {
  type    = string
  default = "pib"
}
variable "environment" {
  type    = string
  default = "dev"
}
variable "location" {
  type    = string
  default = "germanywestcentral"
}
variable "kubernetes_version" {
  type    = string
  default = null
}
variable "node_vm_size" {
  type    = string
  default = "Standard_D2s_v5"
}
variable "enable_bastion" {
  type    = bool
  default = false
}
variable "allowed_ssh_cidr" {
  type    = string
  default = "192.0.2.1/32" # placeholder (TEST-NET), set your own IP when enable_bastion = true
}
variable "ssh_public_key" {
  type    = string
  default = ""
}
