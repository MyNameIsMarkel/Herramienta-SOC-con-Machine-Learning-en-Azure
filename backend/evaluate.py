import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix

model         = joblib.load("model/isolation_forest.pkl")
scaler        = joblib.load("model/scaler.pkl")
feature_names = joblib.load("model/feature_names.pkl")

X_test = pd.read_csv("data/test_data.csv")
X_scaled = scaler.transform(X_test)
y_pred_raw = model.predict(X_scaled)
y_pred = (y_pred_raw == -1).astype(int)

print(f"\nConexiones analizadas : {len(X_test)}")
print(f"Anomalías detectadas  : {y_pred.sum()}")
print(f"Tráfico normal        : {(y_pred == 0).sum()}")

# Si tienes etiquetas reales
try:
    y_true_raw = pd.read_csv("data/test_labels.csv").squeeze()
    y_true = (y_true_raw.str.strip() != 'BENIGN').astype(int)
    print("\nReporte detallado:")
    print(classification_report(y_true, y_pred, target_names=['Normal', 'Ataque']))
except FileNotFoundError:
    print("\n Sin etiquetas reales — solo mostrando predicciones")