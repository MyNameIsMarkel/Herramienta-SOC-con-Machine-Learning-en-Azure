output "resource_group_name" {
  value = azurerm_resource_group.soc_rg.name
}

output "workspace_id" {
  value = azurerm_log_analytics_workspace.law.id
}

output "ml_workspace_name" {
  value = azurerm_machine_learning_workspace.ml_workspace.name
}

output "ml_workspace_id" {
  value = azurerm_machine_learning_workspace.ml_workspace.id
}