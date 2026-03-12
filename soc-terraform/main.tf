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
  location = "Spain Central"  # Cambia si tu región es diferente
}
