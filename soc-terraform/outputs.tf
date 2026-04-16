output "resource_group_name" {
  value = azurerm_resource_group.soc_rg.name
}

output "workspace_id" {
  value = azurerm_log_analytics_workspace.law.id
}