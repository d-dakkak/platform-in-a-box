data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "this" {
  name                          = var.name
  location                      = var.location
  resource_group_name           = var.resource_group_name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "standard"
  rbac_authorization_enabled    = true
  soft_delete_retention_days    = 7
  purge_protection_enabled      = false # dev only; enable for production
  public_network_access_enabled = true  # dev only; use private endpoints for production
  tags                          = var.tags
}

# Whoever runs Terraform may write secrets.
resource "azurerm_role_assignment" "deployer" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# special = false keeps the passwords safe to embed in connection URLs.
resource "random_password" "postgres" {
  length  = 24
  special = false
}

resource "random_password" "rabbitmq" {
  length  = 24
  special = false
}

resource "azurerm_key_vault_secret" "postgres" {
  name         = "postgres-password"
  value        = random_password.postgres.result
  key_vault_id = azurerm_key_vault.this.id
  depends_on   = [azurerm_role_assignment.deployer]
}

resource "azurerm_key_vault_secret" "rabbitmq" {
  name         = "rabbitmq-password"
  value        = random_password.rabbitmq.result
  key_vault_id = azurerm_key_vault.this.id
  depends_on   = [azurerm_role_assignment.deployer]
}
