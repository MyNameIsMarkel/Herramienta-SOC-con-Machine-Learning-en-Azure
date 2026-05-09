# Herramienta SOC con Machine Learning en Azure

Proyecto académico que implementa una herramienta de detección de anomalías de red para un Centro de Operaciones de Seguridad (SOC), integrando Machine Learning con Microsoft Azure y Sentinel.

## Descripción

El sistema analiza tráfico de red utilizando un modelo de Machine Learning entrenado sobre el dataset CIC-IDS2017, detectando patrones anómalos que podrían indicar actividad maliciosa. Cuando se detecta una anomalía, el sistema crea automáticamente un incidente en Microsoft Sentinel y bloquea la IP maliciosa en el firewall de red. La infraestructura completa está desplegada en Azure mediante Terraform.

## Arquitectura

```
Tráfico de red (CIC-IDS2017 · 52 features)
         ↓
Azure Log Analytics Workspace + Microsoft Sentinel
         ↓
Logic App: soc-anomaly-playbook
         ↓
Azure ML Endpoint · Isolation Forest (inferencia <200ms)
         ↓
         ├── anomaly=false → log normal
         └── anomaly=true  → Incidente Sentinel
                             + Logic App: soc-response-playbook
                                    ↓
                             Bloqueo IP en NSG (automático)
```

## Demo

Dashboard en vivo: [https://stsocsmlstorage.z28.web.core.windows.net/](https://stsocsmlstorage.z28.web.core.windows.net/)

## Estructura del proyecto

```
├── soc-terraform/               # Infraestructura como código (Terraform)
│   ├── main.tf                  # RG, Sentinel, ML Workspace, Key Vault, VNet
│   ├── logic_app.tf             # Logic App de detección (Sentinel ↔ ML)
│   ├── playbook_respuesta.tf    # Logic App de respuesta (bloqueo IP en NSG)
│   ├── variables.tf             # Variables de configuración
│   ├── outputs.tf               # Outputs: URLs, IDs de recursos
│   └── .terraform.lock.hcl     # Lock de versiones de providers
│
├── ml-model/                    # Modelo de Machine Learning
│   ├── train.py                 # Entrenamiento Isolation Forest (CIC-IDS2017)
│   ├── score.py                 # Inferencia para el endpoint Azure ML
│   ├── predict.py               # Predicción local sobre CSV
│   ├── evaluate.py              # Evaluación con etiquetas reales
│   ├── deploy.py                # Despliegue del endpoint en Azure ML
│   ├── submit_job.py            # Lanzar entrenamiento como Job en Azure ML
│   ├── conda.yml                # Entorno Conda del endpoint
│   └── requirements.txt         # Dependencias Python
│
├── frontend/
│   └── index.html               # Dashboard SOC (Azure Static Website)
│
└── .github/workflows/
    └── terraform.yml            # CI/CD: Terraform plan/apply en push a main
```

## Tecnologías

| Categoría | Tecnología |
|---|---|
| Cloud | Microsoft Azure (francecentral) |
| IaC | Terraform (azurerm ~> 4.0) |
| ML | Azure Machine Learning · Isolation Forest (scikit-learn) |
| Dataset | CIC-IDS2017 · 52 features de tráfico de red |
| Seguridad | Microsoft Sentinel · Azure Key Vault · NSG |
| Automatización | Azure Logic Apps (2 playbooks) |
| Frontend | HTML/JS · Azure Static Website |
| CI/CD | GitHub Actions · OIDC (sin credenciales) |
| Lenguaje | Python 3.11 |

## Infraestructura desplegada

| Recurso | Nombre | Descripción |
|---|---|---|
| Resource Group | `rg-soc-proyecto` | Contenedor de todos los recursos |
| Log Analytics Workspace | `log-soc-ml` | Base de datos de logs y eventos |
| Microsoft Sentinel | Habilitado sobre LAW | SIEM para detección y gestión de incidentes |
| Azure ML Workspace | `mlw-soc-anomaly` | Entorno de entrenamiento y despliegue ML |
| ML Endpoint | `soc-anomaly-endpoint` | API REST de inferencia (Isolation Forest) |
| Key Vault | `kvsocmlanom` | Almacén de secretos (claves, credenciales) |
| Virtual Network | `vnet-soc-ml` | Red privada con subred dedicada |
| Storage Account | `stsocsmlstorage` | Artefactos ML + hosting del dashboard |
| Logic App (detección) | `soc-anomaly-playbook` | Orquesta Sentinel → ML → Incidente |
| Logic App (respuesta) | `soc-response-playbook` | Bloquea IPs maliciosas en NSG |
| NSG | `nsg-soc-response` | Firewall con reglas de bloqueo automático |
| Application Insights | `appi-soc-ml` | Monitorización del endpoint ML |

## Modelo de Machine Learning

El modelo utiliza **Isolation Forest**, un algoritmo no supervisado de detección de anomalías que no requiere ejemplos etiquetados de ataques para aprender. Aísla puntos de datos: si un punto es fácil de separar del resto, es una anomalía.

| Parámetro | Valor |
|---|---|
| Algoritmo | Isolation Forest |
| Features | 52 (tráfico de red: paquetes, bytes, flags TCP, tiempos IAT...) |
| N° estimadores | 100 |
| Contamination | 0.05 (5% de anomalías esperadas) |
| Dataset | CIC-IDS2017 (Monday — tráfico benigno + ataques) |
| Preprocesado | StandardScaler + eliminación de infinitos y NaNs |

El endpoint devuelve para cada conexión analizada:
```json
[{"anomaly": true, "score": -0.18}]
```
Cuanto más negativo el score, más anómala es la conexión.

## Flujo de detección y respuesta

1. Se recibe una alerta de tráfico de red
2. La Logic App `soc-anomaly-playbook` extrae los datos y llama al endpoint ML
3. El modelo Isolation Forest analiza las 52 features en <200ms
4. Si `anomaly=true` → se crea un incidente en Microsoft Sentinel
5. La Logic App `soc-response-playbook` bloquea la IP en el NSG automáticamente
6. El analista ve el incidente en el dashboard en tiempo real

## Configuración y despliegue

### Prerrequisitos

- Azure CLI (`az login`)
- Terraform >= 1.9
- Python >= 3.8

### Variables de entorno necesarias

```bash
export TF_VAR_ml_endpoint_url="https://soc-anomaly-endpoint.francecentral.inference.ml.azure.com/score"
export TF_VAR_ml_endpoint_key="<clave del endpoint>"
```

### Despliegue de infraestructura

```bash
cd soc-terraform
terraform init
terraform plan
terraform apply
```

### Entrenamiento del modelo

```bash
cd ml-model
pip install -r requirements.txt
python train.py --data_path data/cicids2017_monday.csv --output_path model/
```

### Despliegue del endpoint ML

```bash
cd ml-model
pip install azure-ai-ml azure-identity
python deploy.py
```

### Subir el dashboard

```bash
az storage blob upload \
  --account-name stsocsmlstorage \
  --container-name '$web' \
  --name index.html \
  --file frontend/index.html \
  --content-type "text/html" \
  --auth-mode login
```

### CI/CD

El workflow `.github/workflows/terraform.yml` ejecuta automáticamente `terraform plan` en cada Pull Request y `terraform apply` en cada push a `main`, autenticándose en Azure mediante OIDC (sin credenciales almacenadas).

## Estado del proyecto

- [x] **Infraestructura base** — RG, Log Analytics Workspace, Microsoft Sentinel, VNet desplegados con Terraform en Azure Francia Central
- [x] **Azure ML Workspace** — Workspace con Storage Account, Application Insights y Key Vault
- [x] **Entrenamiento del modelo** — Isolation Forest sobre CIC-IDS2017 con 52 features, entrenado y evaluado localmente
- [x] **Endpoint de inferencia** — Managed Online Endpoint activo en Azure ML, respondiendo en <200ms
- [x] **Secrets en Key Vault** — URL y clave del endpoint almacenadas de forma segura, accesibles mediante Managed Identity
- [x] **Logic App de detección** — `soc-anomaly-playbook` integra Sentinel con el modelo ML y crea incidentes automáticamente
- [x] **Playbook de respuesta** — `soc-response-playbook` bloquea IPs maliciosas en el NSG automáticamente tras confirmar una anomalía
- [x] **Dashboard de monitorización** — Interfaz web pública con métricas en tiempo real, terminal de pruebas y registro de incidentes
- [x] **CI/CD con GitHub Actions** — Pipeline de Terraform con autenticación OIDC sin credenciales hardcodeadas