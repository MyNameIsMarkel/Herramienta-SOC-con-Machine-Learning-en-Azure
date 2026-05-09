from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model, Environment, CodeConfiguration
)
from azure.identity import DefaultAzureCredential

ml_client = MLClient(
    credential=DefaultAzureCredential(),
    subscription_id="b1fca3a5-29b1-49e6-b2dd-6f9cb5dbbc2f",
    resource_group_name="rg-soc-proyecto",
    workspace_name="mlw-soc-anomaly"
)

# 1. Registrar el modelo
model = ml_client.models.create_or_update(
    Model(
        path="./model",
        name="soc-anomaly-detector",
        description="Isolation Forest para detección de anomalías de red SOC"
    )
)
print(f"✅ Modelo registrado: {model.name} v{model.version}")

# 2. Crear el endpoint (solo si no existe)
endpoint = ManagedOnlineEndpoint(
    name="soc-anomaly-endpoint",
    description="Endpoint SOC para detección de anomalías en tiempo real",
    auth_mode="key"
)
try:
    ml_client.online_endpoints.get("soc-anomaly-endpoint")
    print("⏭️  Endpoint ya existe, saltando creación...")
except:
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("✅ Endpoint creado")

# 3. Crear el deployment
deployment = ManagedOnlineDeployment(
    name="blue",
    endpoint_name="soc-anomaly-endpoint",
    model=model,
    code_configuration=CodeConfiguration(
        code="./scoring",
        scoring_script="score.py"
    ),
    environment=Environment(
        conda_file="./scoring/conda.yml",
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
    ),
    instance_type="Standard_F2s_v2",
    instance_count=1
)
ml_client.online_deployments.begin_create_or_update(deployment).result()
print("✅ Deployment completado")

# 4. Asignar tráfico DESPUÉS de que el deployment existe
endpoint = ml_client.online_endpoints.get("soc-anomaly-endpoint")
endpoint.traffic = {"blue": 100}
ml_client.online_endpoints.begin_create_or_update(endpoint).result()
print("🚀 Endpoint activo y recibiendo tráfico al 100%")