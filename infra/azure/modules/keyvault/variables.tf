variable "name" {
  type        = string
  description = "Globally unique, 3-24 characters"
}
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
