import pandas as pd
import numpy as np
import joblib

def predict_traffic(csv_path):
    # Cargar modelo
    model   = joblib.load("model/isolation_forest.pkl")
    scaler  = joblib.load("model/scaler.pkl")
    features = joblib.load("model/feature_names.pkl")

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    X = df[features].replace([np.inf, -np.inf], np.nan).dropna()
    X_scaled = scaler.transform(X)

    # -1 = anomalía, 1 = normal
    predictions = model.predict(X_scaled)
    scores      = model.decision_function(X_scaled)  # Cuanto más negativo, más sospechoso

    df_result = df.loc[X.index].copy()
    df_result['prediction'] = predictions
    df_result['anomaly_score'] = scores
    df_result['is_anomaly'] = predictions == -1

    anomalies = df_result[df_result['is_anomaly']]
    print(f"Anomalías detectadas: {len(anomalies)} de {len(df_result)} conexiones")
    return df_result

if __name__ == "__main__":
    result = predict_traffic("data/nuevo_trafico.csv")
    result.to_csv("output/resultados.csv", index=False)