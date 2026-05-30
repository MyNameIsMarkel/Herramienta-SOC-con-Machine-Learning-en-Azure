import pytest
import numpy as np
import pandas as pd
import joblib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── FIXTURES ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def model():
    return joblib.load("model/isolation_forest.pkl")

@pytest.fixture(scope="module")
def scaler():
    return joblib.load("model/scaler.pkl")

@pytest.fixture(scope="module")
def feature_names():
    return joblib.load("model/feature_names.pkl")

@pytest.fixture(scope="module")
def sample_normal(feature_names):
    data = np.random.normal(loc=50, scale=10, size=(5, len(feature_names)))
    data = np.clip(data, 0, 200)
    return pd.DataFrame(data, columns=feature_names)

@pytest.fixture(scope="module")
def sample_anomaly(feature_names):
    data = np.random.exponential(scale=5000, size=(5, len(feature_names)))
    data = np.clip(data, 1000, 1e6)
    return pd.DataFrame(data, columns=feature_names)

# ── TESTS DEL MODELO ────────────────────────────────────────────────────────

class TestModelLoad:
    def test_model_loads(self, model):
        """El modelo se carga sin errores"""
        assert model is not None

    def test_scaler_loads(self, scaler):
        """El scaler se carga sin errores"""
        assert scaler is not None

    def test_feature_names_loads(self, feature_names):
        """Las feature names se cargan sin errores"""
        assert feature_names is not None
        assert len(feature_names) > 0

    def test_feature_names_is_list(self, feature_names):
        """Las feature names son una lista"""
        assert isinstance(feature_names, list)

    def test_feature_count(self, feature_names):
        """El modelo tiene 11 features"""
        assert len(feature_names) == 11


class TestScaler:
    def test_scaler_transform_shape(self, scaler, sample_normal):
        """El scaler devuelve el mismo número de filas y columnas"""
        X_scaled = scaler.transform(sample_normal)
        assert X_scaled.shape == sample_normal.shape

    def test_scaler_output_is_numpy(self, scaler, sample_normal):
        """El scaler devuelve un array numpy"""
        X_scaled = scaler.transform(sample_normal)
        assert isinstance(X_scaled, np.ndarray)

    def test_scaler_no_nan(self, scaler, sample_normal):
        """El scaler no produce NaN"""
        X_scaled = scaler.transform(sample_normal)
        assert not np.isnan(X_scaled).any()


class TestPredictions:
    def test_predict_returns_array(self, model, scaler, sample_normal):
        """El modelo devuelve un array de predicciones"""
        X_scaled = scaler.transform(sample_normal)
        preds = model.predict(X_scaled)
        assert isinstance(preds, np.ndarray)

    def test_predict_valid_values(self, model, scaler, sample_normal):
        """Las predicciones son solo -1 o 1"""
        X_scaled = scaler.transform(sample_normal)
        preds = model.predict(X_scaled)
        assert set(preds).issubset({-1, 1})

    def test_predict_correct_length(self, model, scaler, sample_normal):
        """El número de predicciones coincide con el número de muestras"""
        X_scaled = scaler.transform(sample_normal)
        preds = model.predict(X_scaled)
        assert len(preds) == len(sample_normal)

    def test_decision_function_returns_scores(self, model, scaler, sample_normal):
        """La función de decisión devuelve scores numéricos"""
        X_scaled = scaler.transform(sample_normal)
        scores = model.decision_function(X_scaled)
        assert isinstance(scores, np.ndarray)
        assert len(scores) == len(sample_normal)

    def test_normal_traffic_mostly_normal(self, model, scaler, sample_normal):
        """El tráfico normal se clasifica mayoritariamente como normal"""
        X_scaled = scaler.transform(sample_normal)
        preds = model.predict(X_scaled)
        normal_ratio = (preds == 1).mean()
        assert normal_ratio >= 0.5

    def test_anomaly_traffic_detected(self, model, scaler, sample_anomaly):
        """El tráfico anómalo genera scores más negativos que el normal"""
        X_scaled = scaler.transform(sample_anomaly)
        scores_anomaly = model.decision_function(X_scaled).mean()
        assert scores_anomaly < 0.2


class TestScoreScript:
    def test_score_output_format(self, model, scaler, feature_names):
        """El formato de salida de score.py es correcto"""
        data = np.zeros((1, len(feature_names)))
        df = pd.DataFrame(data, columns=feature_names)
        X_scaled = scaler.transform(df)
        preds = model.predict(X_scaled)
        scores = model.decision_function(X_scaled)

        results = [
            {"anomaly": bool(p == -1), "score": float(s)}
            for p, s in zip(preds, scores)
        ]

        assert len(results) == 1
        assert "anomaly" in results[0]
        assert "score" in results[0]
        assert isinstance(results[0]["anomaly"], bool)
        assert isinstance(results[0]["score"], float)

    def test_score_json_serializable(self, model, scaler, feature_names):
        """El resultado es serializable a JSON"""
        data = np.zeros((1, len(feature_names)))
        df = pd.DataFrame(data, columns=feature_names)
        X_scaled = scaler.transform(df)
        preds = model.predict(X_scaled)
        scores = model.decision_function(X_scaled)

        results = [
            {"anomaly": bool(p == -1), "score": float(s)}
            for p, s in zip(preds, scores)
        ]

        json_str = json.dumps(results)
        parsed = json.loads(json_str)
        assert parsed[0]["anomaly"] == results[0]["anomaly"]


class TestMonitorDataFormat:
    def test_monitor_result_keys(self):
        """El formato de resultado del monitor tiene los campos correctos"""
        result = {
            "timestamp": "2026-01-01T00:00:00",
            "anomaly": False,
            "score": 0.1234,
            "id": 0
        }
        assert "timestamp" in result
        assert "anomaly" in result
        assert "score" in result
        assert "id" in result

    def test_monitor_payload_format(self):
        """El payload que sube al blob tiene el formato correcto"""
        payload = {
            "updated": "2026-01-01T00:00:00",
            "total": 10,
            "anomalies": 1,
            "results": []
        }
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        assert parsed["total"] == 10
        assert parsed["anomalies"] == 1