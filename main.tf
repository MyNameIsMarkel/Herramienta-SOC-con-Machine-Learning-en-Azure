terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  resource_provider_registrations = "none"
  subscription_id = "b1fca3a5-29b1-49e6-b2dd-6f9cb5dbbc2f"
}


resource "azurerm_resource_group" "soc_rg" {
  name     = "rg-soc-proyecto"
  location = "francecentral"  # Cambia si tu región es diferente
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "law" {
  name                = "log-soc-ml"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 0.5
}

# Microsoft Sentinel (se activa sobre el workspace)
resource "azurerm_sentinel_log_analytics_workspace_onboarding" "sentinel" {
  workspace_id = azurerm_log_analytics_workspace.law.id
}
