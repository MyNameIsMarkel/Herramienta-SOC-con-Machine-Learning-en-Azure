# ── AZURE MONITOR ────────────────────────────────────────────────────────────

# Grupo de acción: a quién notificar
resource "azurerm_monitor_action_group" "soc_alerts" {
  name                = "ag-soc-alertas"
  resource_group_name = azurerm_resource_group.soc_rg.name
  short_name          = "soc-alerts"

  email_receiver {
    name          = "analista-soc"
    email_address = "markel.iturbe@euneiz.es"
  }

  tags = { project = "soc-ml" }
}

# Alerta: Logic App con ejecuciones fallidas
resource "azurerm_monitor_metric_alert" "logic_app_failures" {
  name                = "alert-logicapp-failures"
  resource_group_name = azurerm_resource_group.soc_rg.name
  scopes              = [azurerm_logic_app_workflow.soc_playbook.id]
  description         = "Alerta cuando la Logic App de detección tiene ejecuciones fallidas"
  severity            = 1
  frequency           = "PT5M"
  window_size         = "PT15M"
  enabled             = true

  criteria {
    metric_namespace = "Microsoft.Logic/workflows"
    metric_name      = "RunsFailed"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 0
  }

  action {
    action_group_id = azurerm_monitor_action_group.soc_alerts.id
  }

  tags = { project = "soc-ml" }
}

# Alerta: Application Insights con tasa de errores elevada
resource "azurerm_monitor_metric_alert" "app_insights_errors" {
  name                = "alert-appinsights-errors"
  resource_group_name = azurerm_resource_group.soc_rg.name
  scopes              = [azurerm_application_insights.ml_insights.id]
  description         = "Alerta cuando Application Insights detecta errores en el endpoint ML"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"
  enabled             = true

  criteria {
    metric_namespace = "Microsoft.Insights/components"
    metric_name      = "requests/failed"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 5
  }

  action {
    action_group_id = azurerm_monitor_action_group.soc_alerts.id
  }

  tags = { project = "soc-ml" }
}

# ── OUTPUTS ───────────────────────────────────────────────────────────────────

output "action_group_id" {
  value       = azurerm_monitor_action_group.soc_alerts.id
  description = "ID del grupo de acción para alertas SOC"
}