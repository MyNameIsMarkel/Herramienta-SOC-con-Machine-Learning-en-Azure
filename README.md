# Herramienta SOC con Machine Learning en Azure

Proyecto académico que implementa una herramienta de detección de anomalías de red para un Centro de Operaciones de Seguridad (SOC), integrando Machine Learning con Microsoft Azure y Sentinel.

## Descripción

El sistema analiza tráfico de red en tiempo real utilizando un modelo de Machine Learning entrenado sobre el dataset CIC-IDS2017, detectando patrones anómalos que podrían indicar actividad maliciosa. La infraestructura está desplegada en Azure mediante Terraform.

## Arquitectura

Logs de red
↓
Azure Log Analytics Workspace + Microsoft Sentinel
↓
Azure ML Endpoint (detección de anomalías)
↓
Generación de incidentes en Sentinel

## Estructura del proyecto
├── soc-terraform/ # Infraestructura como código (Terraform)
│ ├── main.tf # Recursos Azure: RG, Sentinel, ML Workspace, Key Vault
│ ├── variables.tf # Variables de configuración
│ ├── outputs.tf # Outputs de Terraform
│ └── terraform.tfvars # Valores de las variables
│
└── ml-model/ # Modelo de Machine Learning
├── train_model.py # Entrenamiento del modelo (Isolation Forest)
├── score.py # Script de inferencia para el endpoint
└── requirements.txt # Dependencias Python

## Tecnologías

- **Cloud**: Microsoft Azure (francecentral)
- **IaC**: Terraform (azurerm ~> 4.0)
- **ML**: Azure Machine Learning, Isolation Forest
- **Seguridad**: Microsoft Sentinel, Azure Key Vault
- **Lenguaje**: Python 3.x

## Infraestructura desplegada

| Recurso | Nombre |
|---|---|
| Resource Group | `rg-soc-proyecto` |
| Log Analytics Workspace | `log-soc-ml` |
| Microsoft Sentinel | Habilitado sobre LAW |
| Azure ML Workspace | `mlw-soc-anomaly` |
| ML Endpoint | `soc-anomaly-endpoint` |
| Key Vault | `kvsocmlanom` |
| Virtual Network | `vnet-soc-ml` |


## Configuración

### Prerrequisitos

- Azure CLI (`az login`)
- Terraform >= 1.0
- Python >= 3.8
- Extensión Azure ML CLI v2 (`az extension add -n ml`)

### Despliegue de infraestructura

```bash
cd soc-terraform
terraform init
terraform plan
terraform apply
```

### Entrenamiento y despliegue del modelo

```bash
cd ml-model
pip install -r requirements.txt
python train_model.py
az ml online-endpoint create --file endpoint.yml ...
```

## Estado del proyecto

- [x] **Infraestructura base (RG, LAW, Sentinel, VNet)** — Despliegue mediante Terraform del Resource Group, Log Analytics Workspace con Microsoft Sentinel habilitado y red virtual con subred dedicada en Azure Francia Central.
- [x] **Azure ML Workspace** — Aprovisionamiento del workspace de Azure Machine Learning junto con sus dependencias: Storage Account, Application Insights y Key Vault.
- [x] **Entrenamiento del modelo (Isolation Forest)** — Entrenamiento de un modelo de detección de anomalías no supervisado sobre el dataset CIC-IDS2017, con 20 features de tráfico de red seleccionadas por importancia.
- [x] **Endpoint de inferencia en Azure ML** — Despliegue del modelo entrenado como Managed Online Endpoint en Azure ML, expuesto como API REST con autenticación por clave.
- [x] **Secrets en Key Vault** — Almacenamiento seguro de la URL y la clave del endpoint ML en Azure Key Vault, con políticas de acceso diferenciadas para el usuario y la Managed Identity del workspace.
- [ ] **Logic App para integración Sentinel ↔ ML** — Automatización del flujo de análisis: la Logic App recibirá alertas de Sentinel, invocará el endpoint ML con los datos del evento y creará incidentes si el modelo detecta anomalía.
- [ ] **Playbook de respuesta automática** — Implementación de acciones de respuesta ante incidentes confirmados, incluyendo notificaciones y bloqueo de IPs maliciosas identificadas por el modelo.
- [ ] **Dashboard de monitorización (Frontend)** — Interfaz web para visualizar en tiempo real los eventos analizados, anomalías detectadas, incidentes generados en Sentinel y métricas del modelo, consumiendo datos desde Log Analytics.