variable "name" {
  type        = string
  description = "Globally unique, 5-50 alphanumeric characters"
}
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
