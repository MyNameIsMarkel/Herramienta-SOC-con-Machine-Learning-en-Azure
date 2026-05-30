# ── AZURE LOGS — CONECTORES DE DATOS ─────────────────────────────────────────

# Conector: Alertas de Azure Security Center → Sentinel
resource "azurerm_sentinel_data_connector_azure_security_center" "asc_connector" {
  name                       = "connector-security-center"
  log_analytics_workspace_id = azurerm_sentinel_log_analytics_workspace_onboarding.sentinel.workspace_id

  depends_on = [azurerm_sentinel_log_analytics_workspace_onboarding.sentinel]
}