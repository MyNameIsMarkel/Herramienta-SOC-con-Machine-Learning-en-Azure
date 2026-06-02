import os
import json
import time
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()

# ── LOGGING ESTRUCTURADO ─────────────────────────────────────────────────────

LOG_WORKSPACE_ID  = os.environ.get("LOG_WORKSPACE_ID", "")
LOG_WORKSPACE_KEY = os.environ.get("LOG_WORKSPACE_KEY", "")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("soc-monitor")

def send_log_analytics(log_type, records):
    """Envía logs a Azure Log Analytics via HTTP Data Collector API."""
    if not LOG_WORKSPACE_ID or not LOG_WORKSPACE_KEY:
        return
    try:
        import hashlib, hmac, base64, requests
        body = json.dumps(records)
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_length = len(body)
        string_to_hash = f"POST\n{content_length}\napplication/json\nx-ms-date:{date}\n/api/logs"
        decoded_key = base64.b64decode(LOG_WORKSPACE_KEY)
        signature = base64.b64encode(
            hmac.new(decoded_key, string_to_hash.encode("utf-8"), digestmod=hashlib.sha256).digest()
        ).decode("utf-8")
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"SharedKey {LOG_WORKSPACE_ID}:{signature}",
            "Log-Type":      log_type,
            "x-ms-date":     date,
        }
        url = f"https://{LOG_WORKSPACE_ID}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"
        requests.post(url, data=body, headers=headers, timeout=10)
    except Exception as e:
        logger.warning(f"No se pudo enviar log a Log Analytics: {e}")

# ── CARGA DEL MODELO ─────────────────────────────────────────────────────────

ACCOUNT_NAME   = "stsocsmlstorage"
CONTAINER_NAME = "$web"
BLOB_NAME      = "results.json"

try:
    model         = joblib.load("model/isolation_forest.pkl")
    scaler        = joblib.load("model/scaler.pkl")
    feature_names = joblib.load("model/feature_names.pkl")
    logger.info("Modelo cargado correctamente")
except FileNotFoundError as e:
    logger.error(f"No se encontró el modelo: {e}")
    raise
except Exception as e:
    logger.error(f"Error cargando el modelo: {e}")
    raise

try:
    blob_client = BlobServiceClient(
        account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
        credential=os.environ.get("STORAGE_KEY", "")
    ).get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
    logger.info("Conexión a Azure Blob Storage establecida")
except Exception as e:
    logger.error(f"Error conectando a Blob Storage: {e}")
    raise

# ── ANÁLISIS DE TRÁFICO ───────────────────────────────────────────────────────

def analizar_trafico():
    logger.debug("Generando vector de tráfico de red")
    n = 20
    n_normal = int(n * 0.85)
    n_ataque = n - n_normal

    normal = np.random.normal(loc=50, scale=10, size=(n_normal, len(feature_names)))
    normal = np.clip(normal, 0, 200)
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
        es_anomalia = bool(pred == -1)
        resultados.append({
            "timestamp": datetime.utcnow().isoformat(),
            "anomaly":   es_anomalia,
            "score":     round(float(score), 4),
            "id":        i
        })
        if es_anomalia:
            logger.warning(f"Anomalía detectada — id={i} score={score:.4f}")
        else:
            logger.debug(f"Tráfico normal — id={i} score={score:.4f}")

    anomalias = [r for r in resultados if r["anomaly"]]
    logger.info(f"Análisis completado: {len(resultados)} conexiones, {len(anomalias)} anomalías")
    return resultados

# ── SUBIR RESULTADOS ──────────────────────────────────────────────────────────

def subir_resultados(resultados, historico):
    historico = (resultados + historico)[:100]
    payload = json.dumps({
        "updated":   datetime.utcnow().isoformat(),
        "total":     len(historico),
        "anomalies": sum(1 for r in historico if r["anomaly"]),
        "results":   historico
    })
    try:
        blob_client.upload_blob(payload, overwrite=True)
        logger.info(f"Subido — {len(resultados)} conexiones, {sum(1 for r in resultados if r['anomaly'])} anomalías")

        send_log_analytics("SOCMonitorLog", [{
            "timestamp":   datetime.utcnow().isoformat(),
            "total":       len(resultados),
            "anomalies":   sum(1 for r in resultados if r["anomaly"]),
            "avg_score":   round(sum(r["score"] for r in resultados) / len(resultados), 4),
            "level":       "INFO"
        }])

        anomalias = [r for r in resultados if r["anomaly"]]
        if anomalias:
            send_log_analytics("SOCAlertLog", [{
                "timestamp": r["timestamp"],
                "score":     r["score"],
                "id":        r["id"],
                "level":     "WARNING"
            } for r in anomalias])

    except Exception as e:
        logger.error(f"Error subiendo resultados al blob: {e}")
        send_log_analytics("SOCErrorLog", [{
            "timestamp": datetime.utcnow().isoformat(),
            "error":     str(e),
            "level":     "ERROR"
        }])

# ── LOOP PRINCIPAL ────────────────────────────────────────────────────────────

INTERVALO = 60
historico = []

logger.info(f"Monitor SOC iniciado — analizando cada {INTERVALO}s")
send_log_analytics("SOCMonitorLog", [{"timestamp": datetime.utcnow().isoformat(), "event": "monitor_started", "level": "INFO"}])

while True:
    try:
        resultados = analizar_trafico()
        subir_resultados(resultados, historico)
        historico = (resultados + historico)[:100]
    except KeyboardInterrupt:
        logger.info("Monitor detenido por el usuario")
        break
    except Exception as e:
        logger.error(f"Error en el ciclo principal: {e}")
        send_log_analytics("SOCErrorLog", [{
            "timestamp": datetime.utcnow().isoformat(),
            "error":     str(e),
            "level":     "ERROR"
        }])
    time.sleep(INTERVALO)