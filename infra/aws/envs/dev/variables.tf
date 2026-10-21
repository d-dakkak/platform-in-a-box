variable "region" {
  type    = string
  default = "eu-central-1"
}
variable "project" {
  type    = string
  default = "pib"
}
variable "environment" {
  type    = string
  default = "dev"
}
variable "github_repository" {
  type        = string
  description = "owner/repo allowed to push images via OIDC, e.g. jane/platform-in-a-box"
}
variable "services" {
  type    = list(string)
  default = ["orders-api", "inventory-worker", "notifier"]
}
variable "enable_eks" {
  type        = bool
  default     = false
  description = "EKS + NAT gateway cost money (~USD 4-5/day). Enable for a few hours, then destroy."
}
variable "kubernetes_version" {
  type    = string
  default = null
}
