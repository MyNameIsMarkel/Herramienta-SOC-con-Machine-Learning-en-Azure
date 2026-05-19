terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Backend remoto — el state persiste entre workflows (apply y destroy comparten el mismo state)
  # REQUISITO: crear el storage account y el container una sola vez antes del primer apply:
  #   az storage account create --name tfstatesocml --resource-group rg-soc-proyecto --location francecentral --sku Standard_LRS
  #   az storage container create --name tfstate --account-name tfstatesocml
  backend "azurerm" {
    use_oidc             = true
    resource_group_name  = "rg-soc-proyecto"
    storage_account_name = "tfstatesocml"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    machine_learning {
      purge_soft_deleted_workspace_on_destroy = true
    }
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    log_analytics_workspace {
      permanently_delete_on_destroy = true
    }
  }
  resource_provider_registrations = "none"
  subscription_id                 = "b1fca3a5-29b1-49e6-b2dd-6f9cb5dbbc2f"
}

# ── DATA SOURCES ────────────────────────────────────────────────────────────
data "azurerm_client_config" "current" {}

# ── RESOURCE GROUP ──────────────────────────────────────────────────────────
resource "azurerm_resource_group" "soc_rg" {
  name     = var.resource_group_name
  location = var.location
}

# ── LOG ANALYTICS + SENTINEL ────────────────────────────────────────────────
resource "azurerm_log_analytics_workspace" "law" {
  name                = var.workspace_name
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 0.5
}

resource "azurerm_sentinel_log_analytics_workspace_onboarding" "sentinel" {
  workspace_id = azurerm_log_analytics_workspace.law.id
}

# ── RED VIRTUAL ──────────────────────────────────────────────────────────────
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-soc-ml"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "subnet_main" {
  name                 = "subnet-soc-main"
  resource_group_name  = azurerm_resource_group.soc_rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# ── AZURE ML: STORAGE ACCOUNT ────────────────────────────────────────────────
resource "azurerm_storage_account" "ml_storage" {
  name                     = "stsocsmlstorage"
  location                 = azurerm_resource_group.soc_rg.location
  resource_group_name      = azurerm_resource_group.soc_rg.name
  account_tier             = "Standard"
  account_replication_type = "LRS"

  static_website {
    index_document = "index.html"
  }
}

# ── AZURE ML: APPLICATION INSIGHTS ───────────────────────────────────────────
resource "azurerm_application_insights" "ml_insights" {
  name                = "appi-soc-ml"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  application_type    = "web"
}

# ── AZURE ML: KEY VAULT ───────────────────────────────────────────────────────
resource "azurerm_key_vault" "ml_kv" {
  name                = "kvsocmlanom"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions      = ["Get", "Set", "List", "Delete", "Purge", "Recover"]
    key_permissions         = ["Get", "List"]
    certificate_permissions = ["Get", "List"]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = "79bd5482-5c3a-45d5-931c-b38641b6aff7"

    secret_permissions      = ["Get", "List", "Set"]
    key_permissions         = ["Get", "List", "WrapKey", "UnwrapKey"]
    certificate_permissions = ["Get", "List"]
  }
}

# ── AZURE ML: WORKSPACE ───────────────────────────────────────────────────────
resource "azurerm_machine_learning_workspace" "ml_workspace" {
  name                    = "mlw-soc-anomaly"
  location                = azurerm_resource_group.soc_rg.location
  resource_group_name     = azurerm_resource_group.soc_rg.name
  application_insights_id = azurerm_application_insights.ml_insights.id
  key_vault_id            = azurerm_key_vault.ml_kv.id
  storage_account_id      = azurerm_storage_account.ml_storage.id

  identity {
    type = "SystemAssigned"
  }

  lifecycle {
    ignore_changes = [
      container_registry_id,
      managed_network,
      tags
    ]
  }
}

resource "azurerm_key_vault_access_policy" "ml_workspace_policy" {
  key_vault_id = azurerm_key_vault.ml_kv.id
  tenant_id    = azurerm_machine_learning_workspace.ml_workspace.identity[0].tenant_id
  object_id    = azurerm_machine_learning_workspace.ml_workspace.identity[0].principal_id

  secret_permissions      = ["Get", "List"]
  key_permissions         = ["Get", "List", "WrapKey", "UnwrapKey"]
  certificate_permissions = ["Get", "List"]
}
