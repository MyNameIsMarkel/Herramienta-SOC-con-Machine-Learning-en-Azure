import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import mlflow.sklearn
import joblib
import os

parser = argparse.ArgumentParser()
parser.add_argument("--data_path",   type=str, default="data/cicids2017_monday.csv")
parser.add_argument("--output_path", type=str, default="model")
args = parser.parse_args()

os.makedirs(args.output_path, exist_ok=True)

df = pd.read_csv(args.data_path)
df.columns = df.columns.str.strip()

labels = df['Label'].str.strip() if 'Label' in df.columns else None
drop_cols = ['Flow ID', 'Source IP', 'Destination IP', 'Timestamp', 'Label']
features = df.drop(columns=[c for c in drop_cols if c in df.columns])
features = features.select_dtypes(include=['number'])
features.replace([np.inf, -np.inf], np.nan, inplace=True)
features.dropna(inplace=True)

X_train, X_test = train_test_split(features, test_size=0.2, random_state=42)

if labels is not None:
    _, y_test = train_test_split(labels.loc[features.index], test_size=0.2, random_state=42)
    y_test.to_csv(os.path.join(args.output_path, "test_labels.csv"), index=False)

X_test.to_csv(os.path.join(args.output_path, "test_data.csv"), index=False)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model",  IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1))
])
pipeline.fit(X_train)

# Guardar en formato MLflow (necesario para registrar en Azure ML)
mlflow.sklearn.save_model(pipeline, os.path.join(args.output_path, "mlflow_model"))

# Mantener feature names por si acaso
joblib.dump(list(features.columns), os.path.join(args.output_path, "feature_names.pkl"))

print(f"Entrenado con {len(X_train)} filas")
print(f"Modelo MLflow guardado en {args.output_path}")
