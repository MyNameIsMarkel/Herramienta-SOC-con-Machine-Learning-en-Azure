output "resource_group_name" {
  value = azurerm_resource_group.soc_rg.name
}

output "workspace_name" {
  value = azurerm_log_analytics_workspace.law.name
}

output "static_web_app_url" {
  value = azurerm_static_web_app.dashboard.default_host_name
}