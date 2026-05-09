# Backend — Modelo de Machine Learning

[← Volver al README principal](../README.md)

Módulo de Machine Learning para detección de anomalías en tráfico de red, basado en el algoritmo Isolation Forest y desplegado como endpoint REST en Azure ML.

## Modelo

| Parámetro | Valor |
|---|---|
| Algoritmo | Isolation Forest |
| Features | 52 (tráfico de red: paquetes, bytes, flags TCP, tiempos IAT...) |
| N° estimadores | 100 |
| Contamination | 0.05 (5% de anomalías esperadas) |
| Dataset | CIC-IDS2017 (Monday — tráfico benigno + ataques) |
| Preprocesado | StandardScaler + eliminación de infinitos y NaNs |

El endpoint devuelve para cada conexión:
```json
[{"anomaly": true, "score": -0.18}]
```
Cuanto más negativo el score, más anómala es la conexión.

## Endpoint en Azure ML

| Campo | Valor |
|---|---|
| Nombre | `soc-anomaly-endpoint` |
| URL | `https://soc-anomaly-endpoint.francecentral.inference.ml.azure.com/score` |
| Autenticación | Bearer token (clave en Key Vault) |
| Región | France Central |

## Estructura

```
backend/
├── train.py          # Entrenamiento del modelo sobre CIC-IDS2017
├── score.py          # Script de inferencia para el endpoint Azure ML
├── predict.py        # Predicción local sobre un CSV
├── evaluate.py       # Evaluación con etiquetas reales
├── deploy.py         # Despliegue del endpoint en Azure ML
├── submit_job.py     # Lanzar entrenamiento como Job en Azure ML
├── conda.yml         # Entorno Conda del endpoint
├── requirements.txt  # Dependencias Python locales
├── model/
│   ├── isolation_forest.pkl   # Modelo entrenado
│   ├── scaler.pkl             # StandardScaler ajustado
│   └── feature_names.pkl      # Lista de las 52 features
└── scoring/
    ├── score.py      # Script de inferencia (versión para el deployment)
    └── conda.yml     # Entorno del deployment
```

## Entrenamiento local

```bash
pip install -r requirements.txt
python train.py --data_path data/cicids2017_monday.csv --output_path model/
```

## Despliegue del endpoint

```bash
pip install azure-ai-ml azure-identity
python deploy.py
```

## Prueba del endpoint

```python
import urllib.request, json, joblib

url = "https://soc-anomaly-endpoint.francecentral.inference.ml.azure.com/score"
key = "<clave del endpoint>"
features = joblib.load("model/feature_names.pkl")

payload = json.dumps({"data": [[0] * len(features)]}).encode()
req = urllib.request.Request(url, data=payload, headers={
    "Content-Type": "application/json",
    "Authorization": f"Bearer {key}"
})
print(urllib.request.urlopen(req).read().decode())
# [{"anomaly": false, "score": 0.216}]
```

## Dataset

El modelo se entrena sobre el dataset **CIC-IDS2017** (Canadian Institute for Cybersecurity). Se usa la captura del lunes que contiene tráfico benigno, lo que permite entrenar el modelo sin etiquetas de ataque (aprendizaje no supervisado).

Los ficheros CSV no están incluidos en el repositorio por su tamaño (>100MB). Descárgalos desde [https://www.unb.ca/cic/datasets/ids-2017.html](https://www.unb.ca/cic/datasets/ids-2017.html) y colócalos en `backend/data/`.