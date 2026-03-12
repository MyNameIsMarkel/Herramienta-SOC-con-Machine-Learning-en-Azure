output "workspace_id" {
  value = azurerm_log_analytics_workspace.law.id
}

output "workspace_name" {
  value = azurerm_log_analytics_workspace.law.name
}

output "sentinel_id" {
  value = azurerm_log_analytics_solution.sentinel.id
}
