# ── LOGIC APP PLAYBOOK ────────────────────────────────────────────────────────

resource "azurerm_logic_app_workflow" "soc_playbook" {
  name                = "soc-anomaly-playbook"
  location            = azurerm_resource_group.soc_rg.location
  resource_group_name = azurerm_resource_group.soc_rg.name

  identity {
    type = "SystemAssigned"
  }

  tags = {
    project = "soc-ml"
  }
}

# ── TRIGGER: HTTP (Sentinel llamará a esta URL) ───────────────────────────────

resource "azurerm_logic_app_trigger_http_request" "sentinel_trigger" {
  name         = "sentinel_alert"
  logic_app_id = azurerm_logic_app_workflow.soc_playbook.id

  schema = jsonencode({
    type = "object"
    properties = {
      AlertName     = { type = "string" }
      AlertSeverity = { type = "string" }
      Description   = { type = "string" }
      WorkspaceId   = { type = "string" }
    }
  })
}

# ── ACCIÓN 1: Llamar al endpoint ML ──────────────────────────────────────────

resource "azurerm_logic_app_action_custom" "call_ml_endpoint" {
  name         = "Call_ML_Endpoint"
  logic_app_id = azurerm_logic_app_workflow.soc_playbook.id

  body = jsonencode({
    type = "Http"
    inputs = {
      method = "POST"
      uri    = var.ml_endpoint_url
      headers = {
        "Content-Type"  = "application/json"
        "Authorization" = "Bearer ${var.ml_endpoint_key}"
      }
      body = {
        data = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
      }
    }
    runAfter = {}
  })
}

# ── ACCIÓN 2: Parsear respuesta del ML ───────────────────────────────────────

resource "azurerm_logic_app_action_custom" "parse_ml_response" {
  name         = "Parse_ML_Response"
  logic_app_id = azurerm_logic_app_workflow.soc_playbook.id

  body = jsonencode({
    type   = "ParseJson"
    inputs = {
      content = "@body('Call_ML_Endpoint')"
      schema = {
        type  = "array"
        items = {
          type = "object"
          properties = {
            anomaly = { type = "boolean" }
            score   = { type = "number" }
          }
        }
      }
    }
    runAfter = {
      Call_ML_Endpoint = ["Succeeded"]
    }
  })

  depends_on = [azurerm_logic_app_action_custom.call_ml_endpoint]
}

# ── ACCIÓN 3: Si anomalía → crear incidente en Sentinel ──────────────────────

resource "azurerm_logic_app_action_custom" "check_anomaly" {
  name         = "Check_If_Anomaly"
  logic_app_id = azurerm_logic_app_workflow.soc_playbook.id

  body = jsonencode({
    type = "If"
    expression = {
      and = [{
        equals = [
          "@body('Parse_ML_Response')?[0]?['anomaly']",
          true
        ]
      }]
    }
    actions = {
      Create_Sentinel_Incident = {
        type = "Http"
        inputs = {
          method = "PUT"
          uri    = "https://management.azure.com/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.soc_rg.name}/providers/Microsoft.OperationalInsights/workspaces/${azurerm_log_analytics_workspace.law.name}/providers/Microsoft.SecurityInsights/incidents/@{guid()}?api-version=2023-02-01"
          headers = {
            "Content-Type" = "application/json"
          }
          body = {
            properties = {
              title       = "@concat('SOC-ML: Anomalia detectada - ', triggerBody()?['AlertName'])"
              description = "@concat('Score: ', string(body('Parse_ML_Response')?[0]?['score']), ' | Origen: ', triggerBody()?['Description'])"
              severity    = "High"
              status      = "New"
            }
          }
          authentication = {
            type     = "ManagedServiceIdentity"
            audience = "https://management.azure.com/"
          }
        }
      }
    }
    else     = { actions = {} }
    runAfter = {
      Parse_ML_Response = ["Succeeded"]
    }
  })

    depends_on = [azurerm_logic_app_action_custom.parse_ml_response]

}

# ── PERMISOS ──────────────────────────────────────────────────────────────────

# La Logic App necesita crear incidentes en Sentinel
resource "azurerm_role_assignment" "logic_app_sentinel_contributor" {
  scope                = azurerm_log_analytics_workspace.law.id
  role_definition_name = "Microsoft Sentinel Contributor"
  principal_id         = azurerm_logic_app_workflow.soc_playbook.identity[0].principal_id
}


# ── AUTOMATION RULE: Sentinel dispara la Logic App ────────────────────────────

resource "azurerm_sentinel_automation_rule" "trigger_ml_playbook" {
  name                       = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
  display_name               = "SOC-ML: Trigger anomaly playbook on alerts"
  order                      = 1
  enabled                    = true

  action_playbook {
    logic_app_id = azurerm_logic_app_workflow.soc_playbook.id
    tenant_id    = data.azurerm_client_config.current.tenant_id
    order        = 1
  }

  depends_on = [azurerm_sentinel_log_analytics_workspace_onboarding.sentinel]
}
