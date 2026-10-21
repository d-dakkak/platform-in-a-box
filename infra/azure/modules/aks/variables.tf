variable "name" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "subnet_id" { type = string }
variable "acr_id" { type = string }
variable "kubernetes_version" {
  type        = string
  default     = null
  description = "null = AKS default. Pin it once the cluster exists."
}
variable "node_vm_size" {
  type    = string
  default = "Standard_D2s_v5"
}
variable "node_min_count" {
  type    = number
  default = 2
}
variable "node_max_count" {
  type    = number
  default = 3
}
variable "tags" {
  type    = map(string)
  default = {}
}
