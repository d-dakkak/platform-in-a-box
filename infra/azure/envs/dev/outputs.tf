output "resource_group" { value = azurerm_resource_group.this.name }
output "aks_name" { value = module.aks.name }
output "acr_name" { value = module.acr.name }
output "acr_login_server" { value = module.acr.login_server }
output "key_vault_uri" { value = module.keyvault.vault_uri }
output "tenant_id" { value = module.keyvault.tenant_id }
output "eso_client_id" { value = azurerm_user_assigned_identity.eso.client_id }
output "bastion_public_ip" { value = try(module.bastion[0].public_ip, null) }
