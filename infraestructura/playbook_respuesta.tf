# ── PLAYBOOK DE RESPUESTA AUTOMÁTICA ─────────────────────────────────────────

# ── NSG PARA BLOQUEO DE IPs ───────────────────────────────────────────────────

resource "azurerm_network_security_group" "soc_response_nsg" {
  name                = "nsg-soc-response"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  tags                = { project = "soc-ml" }
}

# ── LOGIC APP ─────────────────────────────────────────────────────────────────

resource "azurerm_logic_app_workflow" "response_playbook" {
  name                = "soc-response-playbook"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name
  identity { type = "SystemAssigned" }
  tags = { project = "soc-ml" }
}

# ── TRIGGER: HTTP ─────────────────────────────────────────────────────────────

resource "azurerm_logic_app_trigger_http_request" "response_trigger" {
  name         = "incident_confirmed"
  logic_app_id = azurerm_logic_app_workflow.response_playbook.id

  schema = jsonencode({
    type = "object"
    properties = {
      ip          = { type = "string" }
      score       = { type = "number" }
      alertName   = { type = "string" }
      description = { type = "string" }
    }
  })
}

# ── ACCIÓN 1: Bloquear IP añadiendo regla al NSG ──────────────────────────────

resource "azurerm_logic_app_action_custom" "block_ip_nsg" {
  name         = "Block_IP_NSG"
  logic_app_id = azurerm_logic_app_workflow.response_playbook.id

  body = jsonencode({
    type = "Http"
    inputs = {
      method  = "PUT"
      uri     = "https://management.azure.com/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.soc_rg.name}/providers/Microsoft.Network/networkSecurityGroups/nsg-soc-response/securityRules/block-malicious-ip?api-version=2023-05-01"
      headers = { "Content-Type" = "application/json" }
      body = {
        properties = {
          priority                 = 100
          protocol                 = "*"
          sourceAddressPrefix      = "@{triggerBody()?['ip']}"
          sourcePortRange          = "*"
          destinationAddressPrefix = "*"
          destinationPortRange     = "*"
          access                   = "Deny"
          direction                = "Inbound"
          description              = "@concat('Auto-blocked by SOC-ML | score=', string(triggerBody()?['score']))"
        }
      }
      authentication = {
        type     = "ManagedServiceIdentity"
        audience = "https://management.azure.com/"
      }
    }
    runAfter = {}
  })
}

# ── PERMISOS ──────────────────────────────────────────────────────────────────

resource "azurerm_role_assignment" "response_network_contributor" {
  scope                = azurerm_resource_group.soc_rg.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_logic_app_workflow.response_playbook.identity[0].principal_id
}

# ── OUTPUTS ───────────────────────────────────────────────────────────────────

output "response_playbook_name" {
  value = azurerm_logic_app_workflow.response_playbook.name
}

output "response_playbook_trigger_url" {
  value     = azurerm_logic_app_trigger_http_request.response_trigger.callback_url
  sensitive = true
}