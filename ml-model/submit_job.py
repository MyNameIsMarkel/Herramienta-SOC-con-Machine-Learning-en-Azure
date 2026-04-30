from azure.ai.ml import MLClient, command, Input, Output
from azure.ai.ml.entities import AmlCompute, Environment
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential

ml_client = MLClient(
    credential=DefaultAzureCredential(),
    subscription_id="b1fca3a5-29b1-49e6-b2dd-6f9cb5dbbc2f",
    resource_group_name="rg-soc-proyecto",
    workspace_name="mlw-soc-anomaly"
)

# Compute serverless (sin coste cuando no corre)
try:
    ml_client.compute.get("cpu-cluster")
    print("Compute ya existe")
except:
    cluster = AmlCompute(
        name="cpu-cluster",
        size="Standard_DS2_v2",
        min_instances=0,
        max_instances=2,
        idle_time_before_scale_down=120
    )
    ml_client.compute.begin_create_or_update(cluster).result()
    print("Compute creado")

# Entorno desde conda.yml
env = Environment(
    name="soc-anomaly-env",
    conda_file="conda.yml",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04"
)

# Job de entrenamiento
job = command(
    code=".",                          # sube toda la carpeta ml-model/
    command="python train.py --data_path ${{inputs.data}} --output_path ${{outputs.model}}",
    inputs={
        "data": Input(
            type=AssetTypes.URI_FILE,
            path="data/cicids2017_monday.csv"
        )
    },
    outputs={
        "model": Output(type=AssetTypes.URI_FOLDER)
    },
    environment=env,
    compute="cpu-cluster",
    display_name="soc-anomaly-training",
    experiment_name="soc-anomaly-detection"
)

returned_job = ml_client.jobs.create_or_update(job)
print(f"Job enviado: {returned_job.name}")
print(f"URL: {returned_job.studio_url}")