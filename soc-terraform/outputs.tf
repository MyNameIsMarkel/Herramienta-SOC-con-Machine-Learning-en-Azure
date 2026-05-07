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

output "logic_app_name" {
  value = azurerm_logic_app_workflow.soc_playbook.name
}

output "logic_app_trigger_url" {
  description = "URL HTTP para que Sentinel dispare el playbook"
  value       = azurerm_logic_app_trigger_http_request.sentinel_trigger.callback_url
  sensitive   = true
}

output "dashboard_url" {
  description = "URL pública del dashboard"
  value       = azurerm_storage_account.ml_storage.primary_web_endpoint
}