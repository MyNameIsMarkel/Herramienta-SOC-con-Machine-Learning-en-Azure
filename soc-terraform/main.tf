terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "soc_rg" {
  name     = var.resource_group_name
  location = var.location
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "law" {
  name                = var.workspace_name
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30  # Mínimo gratis
  daily_quota_gb      = 0.5 # Limita el gasto — crítico para créditos
}

# Microsoft Sentinel (se activa sobre el workspace)
resource "azurerm_log_analytics_solution" "sentinel" {
  solution_name         = "SecurityInsights"
  location              = azurerm_resource_group.soc_rg.location
  resource_group_name   = azurerm_resource_group.soc_rg.name
  workspace_resource_id = azurerm_log_analytics_workspace.law.id
  workspace_name        = azurerm_log_analytics_workspace.law.name

  plan {
    publisher = "Microsoft"
    product   = "OMSGallery/SecurityInsights"
  }
}

# Logic App (Playbook para bloqueo automático de IPs)
resource "azurerm_logic_app_workflow" "block_ip_playbook" {
  name                = "playbook-block-ip"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
}

# Regla de alerta en Sentinel (ejemplo: detección de ataques)
resource "azurerm_sentinel_alert_rule_scheduled" "ml_alert" {
  name                       = "ml-anomaly-detection-alert"
  log_analytics_workspace_id = azurerm_log_analytics_solution.sentinel.workspace_resource_id
  display_name               = "ML Anomaly Detected"
  severity                   = "High"
  query                      = <<QUERY
    SecurityEvent
    | where EventID == 4625
    | summarize count() by IpAddress, bin(TimeGenerated, 5m)
    | where count_ > 10
  QUERY
  query_frequency            = "PT5M"
  query_period               = "PT5M"
  trigger_operator           = "GreaterThan"
  trigger_threshold          = 0
  enabled                    = true
}
