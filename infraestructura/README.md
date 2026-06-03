# Infraestructura — Terraform en Azure

[← Volver al README principal](../README.md)

Infraestructura completa del proyecto desplegada en Microsoft Azure mediante Terraform, siguiendo el paradigma de Infraestructura como Código (IaC).

## Recursos desplegados

| Recurso | Nombre | Descripción |
|---|---|---|
| Resource Group | `rg-soc-proyecto` | Contenedor de todos los recursos |
| Log Analytics Workspace | `log-soc-ml` | Base de datos de logs y eventos |
| Microsoft Sentinel | Habilitado sobre LAW | SIEM para detección y gestión de incidentes |
| Azure ML Workspace | `mlw-soc-anomaly` | Entorno de entrenamiento y despliegue ML |
| ML Endpoint | `soc-anomaly-endpoint` | API REST de inferencia (Isolation Forest) |
| Key Vault | `kvsocmlanom` | Almacén de secretos |
| Virtual Network | `vnet-soc-ml` | Red privada con subred dedicada |
| Storage Account | `stsocsmlstorage` | Artefactos ML + hosting del dashboard |
| Logic App (detección) | `soc-anomaly-playbook` | Orquesta Sentinel → ML → Incidente |
| Logic App (respuesta) | `soc-response-playbook` | Bloquea IPs maliciosas en NSG |
| NSG | `nsg-soc-response` | Firewall con reglas de bloqueo automático |
| Application Insights | `appi-soc-ml` | Monitorización del endpoint ML |

## Estructura

```
infraestructura/
├── main.tf                 # RG, Sentinel, ML Workspace, Key Vault, VNet, Storage
├── logic_app.tf            # Logic App de detección (soc-anomaly-playbook)
├── playbook_respuesta.tf   # Logic App de respuesta (soc-response-playbook)
├── variables.tf            # Variables de configuración
├── outputs.tf              # Outputs: URLs, IDs de recursos
└── .terraform.lock.hcl    # Lock de versiones de providers
```

## Variables requeridas

Las siguientes variables deben pasarse como variables de entorno (no en ficheros):

```bash
export TF_VAR_ml_endpoint_url="https://soc-anomaly-endpoint.francecentral.inference.ml.azure.com/score"
export TF_VAR_ml_endpoint_key="<clave del endpoint ML>"
```

## Despliegue

```bash
cd infraestructura
terraform init
terraform plan
terraform apply
```

## CI/CD

El workflow `.github/workflows/terraform.yml` ejecuta automáticamente:
- `terraform plan` en cada Pull Request a `main`
- `terraform apply` en cada push a `main`

La autenticación con Azure se realiza mediante **OIDC** (OpenID Connect), sin credenciales almacenadas en GitHub. Las variables de entorno necesarias se configuran en los secretos del repositorio:

| Variable de GitHub | Descripción |
|---|---|
| `AZURE_CLIENT_ID` | Client ID de la app registration |
| `AZURE_TENANT_ID` | Tenant ID de EUNEIZ |
| `AZURE_SUBSCRIPTION_ID` | ID de la suscripción |

## Secretos en Key Vault

Los secretos del sistema se almacenan en `kvsocmlanom` y se leen desde Terraform mediante data sources:

| Secreto | Descripción |
|---|---|
| `brevo-api-key` | Clave API de Brevo (notificaciones) |
| `gmail-address` | Dirección de email del analista SOC |

## Outputs

Tras el despliegue, Terraform muestra:

```
dashboard_url                 = "https://stsocsmlstorage.z28.web.core.windows.net/"
logic_app_name                = "soc-anomaly-playbook"
logic_app_trigger_url         = <sensitive>
ml_workspace_name             = "mlw-soc-anomaly"
response_playbook_name        = "soc-response-playbook"
response_playbook_trigger_url = <sensitive>
```

## Autenticación CI/CD — Managed Identity

La autenticación de GitHub Actions con Azure se realiza mediante una **User Assigned Managed Identity** con federated credentials, sin necesidad de client secrets ni App Registrations con permisos de administrador.

| Recurso | Valor |
|---|---|
| Nombre | `github-actions-identity` |
| Client ID | `412e9fb1-ac39-4e4a-95bc-528e18693a9e` |
| Principal ID | `0f8bfa01-82f9-41b8-b5f2-d884db8b6952` |
| Rol en suscripción | Contributor |
| Rol en Storage | Storage Blob Data Contributor |

Este recurso se creó manualmente fuera de Terraform porque la suscripción académica de EUNEIZ no permite crear App Registrations desde la CLI ni el portal, pero sí permite crear Managed Identities como recursos de Azure normales.

### Variables requeridas en GitHub

| Variable | Valor |
|---|---|
| `AZURE_CLIENT_ID` | `412e9fb1-ac39-4e4a-95bc-528e18693a9e` |
| `ARM_TENANT_ID` | `78f3a279-48c8-4670-9162-a63c451c9fae` |
| `ARM_SUBSCRIPTION_ID` | `b1fca3a5-29b1-49e6-b2dd-6f9cb5dbbc2f` |


## Queries KQL — Azure Log Analytics

Queries útiles para analizar los logs del sistema SOC desde Log Analytics Workspace (`log-soc-ml`).

### Incidentes generados por el modelo ML

```kql
SecurityIncident
| where Title contains "SOC-ML"
| project TimeGenerated, Title, Severity, Status, Description
| order by TimeGenerated desc
| take 50
```

### Ejecuciones de la Logic App en las últimas 24h

```kql
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.LOGIC"
| where ResourceType == "WORKFLOWS"
| where TimeGenerated > ago(24h)
| project TimeGenerated, resource_workflowName_s, status_s, code_s
| order by TimeGenerated desc
```

### Anomalías detectadas por hora

```kql
SecurityIncident
| where Title contains "SOC-ML"
| where TimeGenerated > ago(7d)
| summarize Anomalias = count() by bin(TimeGenerated, 1h)
| render timechart
```

### Errores del endpoint ML en Application Insights

```kql
requests
| where success == false
| where timestamp > ago(24h)
| project timestamp, name, resultCode, duration, url
| order by timestamp desc
```

### Actividad de bloqueo de IPs en el NSG

```kql
AzureDiagnostics
| where Category == "NetworkSecurityGroupRuleCounter"
| where ResourceGroup == "rg-soc-proyecto"
| where TimeGenerated > ago(24h)
| project TimeGenerated, ruleName_s, primaryIPv4Address_s, matchedConnections_d
| order by TimeGenerated desc
```