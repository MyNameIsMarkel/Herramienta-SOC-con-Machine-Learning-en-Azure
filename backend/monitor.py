import json
import time
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from azure.storage.blob import BlobServiceClient

# Cargar modelo
model         = joblib.load("model/isolation_forest.pkl")
scaler        = joblib.load("model/scaler.pkl")
feature_names = joblib.load("model/feature_names.pkl")

# Conexión al blob storage
ACCOUNT_NAME   = "stsocsmlstorage"
CONTAINER_NAME = "$web"
BLOB_NAME      = "results.json"

blob_client = BlobServiceClient(
    account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
    credential=os.environ.get("STORAGE_KEY", "")
).get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)

def analizar_trafico():
    n = 20
    # 85% tráfico normal (valores bajos y estables)
    n_normal = int(n * 0.85)
    n_ataque = n - n_normal

    normal = np.random.normal(loc=50, scale=10, size=(n_normal, len(feature_names)))
    normal = np.clip(normal, 0, 200)

    # 15% tráfico anómalo (valores extremos)
    ataque = np.random.exponential(scale=5000, size=(n_ataque, len(feature_names)))
    ataque = np.clip(ataque, 1000, 1e6)

    datos = np.vstack([normal, ataque])
    np.random.shuffle(datos)

    df = pd.DataFrame(datos, columns=feature_names)
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    X_scaled    = scaler.transform(df)
    predictions = model.predict(X_scaled)
    scores      = model.decision_function(X_scaled)

    resultados = []
    for i, (pred, score) in enumerate(zip(predictions, scores)):
        resultados.append({
            "timestamp": datetime.utcnow().isoformat(),
            "anomaly":   bool(pred == -1),
            "score":     round(float(score), 4),
            "id":        i
        })
    return resultados

def subir_resultados(resultados, historico):
    historico = (resultados + historico)[:100]  # máximo 100 entradas
    payload = json.dumps({
        "updated":   datetime.utcnow().isoformat(),
        "total":     len(historico),
        "anomalies": sum(1 for r in historico if r["anomaly"]),
        "results":   historico
    })
    blob_client.upload_blob(payload, overwrite=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Subido — {len(resultados)} conexiones analizadas, {sum(1 for r in resultados if r['anomaly'])} anomalías")

INTERVALO = 60  # segundos entre análisis
historico = []

print(f"Monitor SOC iniciado — analizando cada {INTERVALO}s")
while True:
    try:
        resultados = analizar_trafico()
        subir_resultados(resultados, historico)
        historico = (resultados + historico)[:100]
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(INTERVALO)