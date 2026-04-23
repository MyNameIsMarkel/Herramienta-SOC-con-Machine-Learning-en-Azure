import json
import joblib
import numpy as np
import pandas as pd
import os

def init():
    global model, scaler, feature_names
    model_path = os.path.join(os.environ["AZUREML_MODEL_DIR"], "model")
    model        = joblib.load(os.path.join(model_path, "isolation_forest.pkl"))
    scaler       = joblib.load(os.path.join(model_path, "scaler.pkl"))
    feature_names = joblib.load(os.path.join(model_path, "feature_names.pkl"))

def run(raw_data):
    data = json.loads(raw_data)
    df   = pd.DataFrame(data["data"], columns=feature_names)
    df   = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    X_scaled    = scaler.transform(df)
    predictions = model.predict(X_scaled)
    scores      = model.decision_function(X_scaled)

    results = [
        {"anomaly": bool(p == -1), "score": float(s)}
        for p, s in zip(predictions, scores)
    ]
    return json.dumps(results)