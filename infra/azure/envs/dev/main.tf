locals {
  name = "${var.project}-${var.environment}"
  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.name}"
  location = var.location
  tags     = local.tags
}

module "network" {
  source              = "../../modules/network"
  name                = local.name
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.tags
}

module "acr" {
  source              = "../../modules/acr"
  name                = "${var.project}${var.environment}${random_string.suffix.result}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.tags
}

module "aks" {
  source              = "../../modules/aks"
  name                = "aks-${local.name}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  subnet_id           = module.network.aks_subnet_id
  acr_id              = module.acr.id
  kubernetes_version  = var.kubernetes_version
  node_vm_size        = var.node_vm_size
  tags                = local.tags
}

module "keyvault" {
  source              = "../../modules/keyvault"
  name                = "kv-${local.name}-${random_string.suffix.result}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.tags
}

# Identity used by the External Secrets Operator to read Key Vault (workload identity, no secrets).
resource "azurerm_user_assigned_identity" "eso" {
  name                = "id-eso-${local.name}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.tags
}

resource "azurerm_federated_identity_credential" "eso" {
  name      = "external-secrets"
  parent_id = azurerm_user_assigned_identity.eso.id
  audience  = ["api://AzureADTokenExchange"]
  issuer    = module.aks.oidc_issuer_url
  subject   = "system:serviceaccount:external-secrets:external-secrets"
}

resource "azurerm_role_assignment" "eso_reads_keyvault" {
  scope                = module.keyvault.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.eso.principal_id
}

module "bastion" {
  count               = var.enable_bastion ? 1 : 0
  source              = "../../modules/bastion"
  name                = local.name
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name
  subnet_id           = module.network.mgmt_subnet_id
  ssh_public_key      = var.ssh_public_key
  allowed_ssh_cidr    = var.allowed_ssh_cidr
  tags                = local.tags
}
