import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import mlflow
import mlflow.sklearn
import joblib
import os

parser = argparse.ArgumentParser()
parser.add_argument("--data_path",   type=str, default="data/cicids2017_monday.csv")
parser.add_argument("--output_path", type=str, default="model")
parser.add_argument("--n_estimators",  type=int,   default=100)
parser.add_argument("--contamination", type=float, default=0.05)
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

# MLflow run explícito → Azure ML lo registra como experimento
mlflow.sklearn.autolog(log_models=False)

with mlflow.start_run():
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  IsolationForest(
            n_estimators=args.n_estimators,
            contamination=args.contamination,
            random_state=42,
            n_jobs=-1
        ))
    ])
    pipeline.fit(X_train)

    # Métricas básicas del modelo
    scores = pipeline.decision_function(X_test)
    preds  = pipeline.predict(X_test)
    anomaly_ratio = (preds == -1).mean()

    mlflow.log_params({
        "n_estimators":  args.n_estimators,
        "contamination": args.contamination,
        "train_rows":    len(X_train),
        "n_features":    X_train.shape[1],
    })
    mlflow.log_metrics({
        "anomaly_ratio_test": float(anomaly_ratio),
        "mean_anomaly_score": float(scores.mean()),
    })

    # Guardar modelo en formato MLflow
    mlflow.sklearn.save_model(pipeline, os.path.join(args.output_path, "mlflow_model"))
    # Guardar también los pkl individuales que necesita score.py
    scaler_fitted = pipeline.named_steps["scaler"]
    model_fitted  = pipeline.named_steps["model"]
    joblib.dump(scaler_fitted, os.path.join(args.output_path, "scaler.pkl"))
    joblib.dump(model_fitted,  os.path.join(args.output_path, "isolation_forest.pkl"))

    # Feature names para inferencia posterior
    joblib.dump(list(features.columns), os.path.join(args.output_path, "feature_names.pkl"))

    print(f"Entrenado con {len(X_train)} filas, {X_train.shape[1]} features")
    print(f"Anomaly ratio en test: {anomaly_ratio:.3%}")
    print(f"Modelo guardado en {args.output_path}/mlflow_model")