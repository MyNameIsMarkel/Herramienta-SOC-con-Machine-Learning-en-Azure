import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

df = pd.read_csv("data/cicids2017_monday.csv")
df.columns = df.columns.str.strip()

# Separar etiquetas
labels = df['Label'].str.strip() if 'Label' in df.columns else None

drop_cols = ['Flow ID', 'Source IP', 'Destination IP', 'Timestamp', 'Label']
features = df.drop(columns=[c for c in drop_cols if c in df.columns])

# Eliminar TODAS las columnas que no sean numéricas (por si hay más texto)
features = features.select_dtypes(include=['number'])

features.replace([np.inf, -np.inf], np.nan, inplace=True)
features.dropna(inplace=True)

# Dividir 80/20 — guarda el 20% para evaluate.py
X_train, X_test = train_test_split(features, test_size=0.2, random_state=42)

# Si tienes etiquetas, guardarlas también para el test
if labels is not None:
    _, y_test = train_test_split(labels.loc[features.index], test_size=0.2, random_state=42)
    y_test.to_csv("data/test_labels.csv", index=False)

X_test.to_csv("data/test_data.csv", index=False)

# Entrenar solo con el 80%
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
model.fit(X_train_scaled)

joblib.dump(model, "model/isolation_forest.pkl")
joblib.dump(scaler, "model/scaler.pkl")
joblib.dump(list(features.columns), "model/feature_names.pkl")

print(f"Entrenado con {len(X_train)} filas")
print(f"Test guardado en data/test_data.csv ({len(X_test)} filas)")