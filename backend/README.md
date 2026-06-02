# Backend — Modelo de Machine Learning

[← Volver al README principal](../README.md)

Módulo de Machine Learning para detección de anomalías en tráfico de red, basado en el algoritmo Isolation Forest.

## Modelo

| Parámetro | Valor |
|---|---|
| Algoritmo | Isolation Forest |
| Features | 11 (tráfico de red: puertos, bytes, tiempos, frecuencias...) |
| N° estimadores | 100 |
| Contamination | 0.05 (5% de anomalías esperadas) |
| Dataset | Capturas reales de red (Wireshark + CIC-IDS2017) |
| Preprocesado | StandardScaler + eliminación de infinitos y NaNs |

El modelo devuelve para cada conexión:
```json
{"anomaly": true, "score": -0.18}
```
Cuanto más negativo el score, más anómala es la conexión.

## Monitor en tiempo real

El script `monitor.py` analiza tráfico cada 60 segundos y sube los resultados a Azure Blob Storage, donde el dashboard los recoge automáticamente.

```bash
# Arrancar el monitor
cd backend
python monitor.py
```

Requiere el archivo `.env`:
STORAGE_KEY=<clave del storage account de Azure>

## Estructura
```bash
backend/
├── train.py          # Entrenamiento del modelo
├── score.py          # Script de inferencia para Azure ML
├── monitor.py        # Monitor local con inferencia en tiempo real
├── predict.py        # Predicción local sobre un CSV
├── evaluate.py       # Evaluación con etiquetas reales
├── deploy.py         # Despliegue del endpoint en Azure ML
├── requirements.txt  # Dependencias Python
├── .env              # Variables de entorno (NO subir a Git)
├── model/
│   ├── isolation_forest.pkl   # Modelo entrenado
│   ├── scaler.pkl             # StandardScaler ajustado
│   └── feature_names.pkl      # Lista de las 11 features
├── scoring/
│   ├── score.py      # Script de inferencia para Azure ML deployment
│   └── conda.yml     # Entorno del deployment
└── tests/
├── test_model.py        # 18 tests unitarios
└── test_integracion.py  # 6 tests de integración
```

## Tests

```bash
# Ejecutar todos los tests
cd backend
pytest tests/ -v

# Solo unitarios
pytest tests/test_model.py -v

# Solo integración
pytest tests/test_integracion.py -v
```

### Cobertura de tests

| Suite | Tests | Qué verifica |
|---|---|---|
| `TestModelLoad` | 5 | Carga correcta de los pkl |
| `TestScaler` | 3 | Transformación del scaler |
| `TestPredictions` | 6 | Predicciones válidas del modelo |
| `TestScoreScript` | 2 | Formato JSON de salida |
| `TestMonitorDataFormat` | 2 | Formato del payload del monitor |
| `TestFlujoInferencia` | 3 | Flujo completo datos→modelo→JSON |
| `TestFlujoMonitor` | 3 | Ciclo completo del monitor |

## Entrenamiento local

```bash
pip install -r requirements.txt
python train.py --data_path data/tu_dataset.csv --output_path model/
```

## Dataset

Los ficheros CSV no están incluidos en el repositorio por su tamaño. El modelo actual fue entrenado con capturas reales de tráfico de red con 11 features: `No., Time, Length, cumilative_bytes, delta time, fw1_mon_if/dir, freq, RSSI, TX rate, packet length, rel_time`.
