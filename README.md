Gestión por ramas y Pull Requests

```bash
Monitor local (Python · Isolation Forest)
↓ cada 60s
Azure Blob Storage (results.json)
↓ cada 30s
Dashboard web (Azure Static Website)
↓ botones de prueba
Logic App: soc-anomaly-playbook
↓
Azure ML Endpoint · Isolation Forest (inferencia)
↓
├── anomaly=false → log normal
└── anomaly=true  → Incidente Sentinel
+ Logic App: soc-response-playbook
↓
Bloqueo IP en NSG (automático)
```

## Arquitectura de Azure
![imagen que muestra la Arquitectura de Azure](infraestructura/arquitectura-azure.png)

## Demo

Dashboard en vivo: [https://stsocsmlstorage.z28.web.core.windows.net/](https://stsocsmlstorage.z28.web.core.windows.net/)

## Documentación por módulo

| Módulo | Descripción | Documentación |
|---|---|---|
| `frontend/` | Dashboard web de monitorización en tiempo real | [README →](./frontend/README.md) |
| `backend/` | Modelo Isolation Forest · entrenamiento e inferencia | [README →](./backend/README.md) |
| `infraestructura/` | Infraestructura Azure como código (Terraform) | [README →](./infraestructura/README.md) |

## Tecnologías

| Categoría | Tecnología |
|---|---|
| Cloud | Microsoft Azure (francecentral) |
| IaC | Terraform (azurerm ~> 4.0) |
| ML | Isolation Forest (scikit-learn) |
| Dataset | Capturas reales de red Wireshark (11 features) |
| Seguridad | Microsoft Sentinel · Azure Key Vault · NSG |
| Automatización | Azure Logic Apps (2 playbooks) |
| Monitorización | Azure Monitor · Application Insights · Azure Logs |
| Frontend | HTML/JS · Azure Static Website |
| CI/CD | GitHub Actions · OIDC · Managed Identity |
| Testing | pytest · pre-commit hooks |
| Lenguaje | Python 3.11 |

## Estado del proyecto

- [x] Infraestructura base — RG, Log Analytics, Sentinel, VNet
- [x] Azure ML Workspace con dependencias
- [x] Entrenamiento Isolation Forest sobre datos reales de red
- [x] Monitor local con inferencia ML en tiempo real
- [x] Logging estructurado DEBUG/INFO/WARNING/ERROR → Log Analytics
- [x] Results subidos a Azure Blob Storage cada 60s
- [x] Secrets en Key Vault con Managed Identity
- [x] Logic App de detección (Sentinel ↔ ML ↔ Incidentes)
- [x] Playbook de respuesta automática (bloqueo IP en NSG)
- [x] Dashboard de monitorización (Azure Static Website)
- [x] CI/CD con GitHub Actions y autenticación OIDC via Managed Identity
- [x] Azure Monitor con alertas métricas
- [x] Azure Logs con conectores de datos Sentinel
- [x] Tests unitarios (pytest · 18 tests)
- [x] Test de integración (pytest · 6 tests)
- [x] Pre-commit hooks (tests automáticos antes de cada commit)
- [x] Secret scanning (GitHub Advanced Security)

## Arrancar el monitor local

```bash
cd backend
python monitor.py
```

Requiere el archivo `backend/.env` con:
```bash
STORAGE_KEY=<clave del storage account>
LOG_WORKSPACE_ID=<id del log analytics workspace>
LOG_WORKSPACE_KEY=<clave del log analytics workspace>
```

## Ejecutar los tests

```bash
cd backend
pytest tests/ -v
```

## Nota sobre los GitHub Actions workflows

| Workflow | Trigger | Descripción |
|---|---|---|
| `Tests` | Push / PR automático | 24 tests unitarios e integración |
| `Apply — Todo el proyecto` | Manual | Infraestructura + frontend + backend |
| `Apply — Solo infraestructura` | Manual | Terraform apply |
| `Apply — Frontend` | Manual | Sube dashboard al Storage |
| `Apply — Backend` | Manual | Entrena modelo y pasa tests |
| `Destroy — Todo el proyecto` | Manual | Elimina toda la infraestructura |
| `Destroy — Solo infraestructura` | Manual | Terraform destroy |
| `Destroy — Frontend` | Manual | Elimina dashboard del Storage |
| `Destroy — Backend` | Manual | Elimina endpoint y modelo ML |
| `Terraform Apply` | Manual | Apply con imports de recursos existentes |
| `Terraform Destroy` | Manual | Destroy completo |

La autenticación con Azure se realiza mediante **OIDC con Managed Identity** (`github-actions-identity`) sin necesidad de client secrets. La Managed Identity tiene rol **Contributor** en la suscripción y **Storage Blob Data Contributor** en el storage account.

### Crear la Managed Identity (solo una vez)

```bash
az identity create --name "github-actions-identity" --resource-group rg-soc-proyecto
az role assignment create --assignee "<principalId>" --role Contributor --scope /subscriptions/<subscriptionId>
az role assignment create --assignee "<principalId>" --role "Storage Blob Data Contributor" --scope /subscriptions/<subscriptionId>/resourceGroups/rg-soc-proyecto/providers/Microsoft.Storage/storageAccounts/stsocsmlstorage
az identity federated-credential create --name "github-main" --identity-name "github-actions-identity" --resource-group rg-soc-proyecto --issuer "https://token.actions.githubusercontent.com" --subject "repo:<org>/<repo>:ref:refs/heads/main" --audiences "api://AzureADTokenExchange"
az identity federated-credential create --name "github-pr" --identity-name "github-actions-identity" --resource-group rg-soc-proyecto --issuer "https://token.actions.githubusercontent.com" --subject "repo:<org>/<repo>:pull_request" --audiences "api://AzureADTokenExchange"
```