from azure.ai.ml import MLClient, command, Input
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Environment

ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id="b1fca3a5-29b1-49e6-b2dd-6f9cb5dbbc2f",
    resource_group_name="rg-soc-proyecto",
    workspace_name="mlw-soc-anomaly"
)

# Registrar el entorno en el workspace antes de usarlo
env = Environment(
    name="soc-anomaly-env",
    version="1",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
    conda_file="conda.yml",
    description="Entorno SOC con scikit-learn e Isolation Forest"
)
ml_client.environments.create_or_update(env)  # <-- línea clave que faltaba

job = command(
    code="./",
    command="python train.py --data_path ${{inputs.train_data}} --output_path ./outputs --n_estimators 100 --contamination 0.05",
    inputs={
        "train_data": Input(
            type=AssetTypes.URI_FILE,
            path="azureml:soc-train-data:1"
        )
    },
    environment="azureml:soc-anomaly-env:1",  # referencia por nombre tras registrarlo
    compute="cpu-soc-cluster",
    display_name="soc-isolation-forest-v1",
    experiment_name="soc-anomaly-detection",
    description="Entrenamiento Isolation Forest con CICIDS2017 Monday"
)

returned_job = ml_client.jobs.create_or_update(job)
print(f"Job lanzado: {returned_job.name}")
print(f"Estado:      {returned_job.status}")
print(f"Studio URL:  {returned_job.studio_url}")