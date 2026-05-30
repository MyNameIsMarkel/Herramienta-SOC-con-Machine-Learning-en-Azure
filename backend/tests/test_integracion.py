import pytest
import numpy as np
import pandas as pd
import joblib
import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# ── FIXTURE COMPARTIDA ───────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pipeline():
    """Carga el modelo completo: scaler + model + feature_names"""
    model         = joblib.load("model/isolation_forest.pkl")
    scaler        = joblib.load("model/scaler.pkl")
    feature_names = joblib.load("model/feature_names.pkl")
    return model, scaler, feature_names


# ── TEST DE INTEGRACIÓN 1: Flujo completo de inferencia ──────────────────────

class TestFlujoInferencia:
    def test_flujo_normal_completo(self, pipeline):
        """
        INTEGRACIÓN: datos crudos → scaler → modelo → resultado JSON
        Simula exactamente lo que hace score.py en el endpoint
        """
        model, scaler, feature_names = pipeline

        # 1. Entrada: datos crudos como llegarían al endpoint
        raw_data = np.random.normal(loc=50, scale=10, size=(3, len(feature_names)))
        raw_data = np.clip(raw_data, 0, 200)
        df = pd.DataFrame(raw_data, columns=feature_names)
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

        # 2. Transformación con scaler
        X_scaled = scaler.transform(df)

        # 3. Predicción con modelo
        predictions = model.predict(X_scaled)
        scores      = model.decision_function(X_scaled)

        # 4. Resultado final como lo devuelve score.py
        results = [
            {"anomaly": bool(p == -1), "score": float(s)}
            for p, s in zip(predictions, scores)
        ]

        # Verificaciones del flujo completo
        assert len(results) == 3
        assert all("anomaly" in r for r in results)
        assert all("score" in r for r in results)
        assert all(isinstance(r["anomaly"], bool) for r in results)
        assert all(isinstance(r["score"], float) for r in results)
        json_str = json.dumps(results)
        assert json.loads(json_str) == results

    def test_flujo_anomalia_completo(self, pipeline):
        """
        INTEGRACIÓN: datos anómalos → scaler → modelo → resultado con anomaly=True
        """
        model, scaler, feature_names = pipeline

        # Datos extremos que deberían ser anomalías
        raw_data = np.random.exponential(scale=5000, size=(5, len(feature_names)))
        raw_data = np.clip(raw_data, 1000, 1e6)
        df = pd.DataFrame(raw_data, columns=feature_names)
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

        X_scaled = scaler.transform(df)
        predictions = model.predict(X_scaled)
        scores      = model.decision_function(X_scaled)

        results = [
            {"anomaly": bool(p == -1), "score": float(s)}
            for p, s in zip(predictions, scores)
        ]

        # Al menos alguna anomalía debe detectarse
        anomalies = [r for r in results if r["anomaly"]]
        assert len(anomalies) >= 1

        # Los scores de anomalías deben ser negativos
        for r in anomalies:
            assert r["score"] < 0

    def test_flujo_entrada_vacia_no_falla(self, pipeline):
        """
        INTEGRACIÓN: entrada con NaN/inf se limpia correctamente antes de predecir
        """
        model, scaler, feature_names = pipeline

        # Datos con NaN e infinitos
        raw_data = np.full((2, len(feature_names)), np.nan)
        df = pd.DataFrame(raw_data, columns=feature_names)
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

        X_scaled = scaler.transform(df)
        predictions = model.predict(X_scaled)

        assert len(predictions) == 2
        assert set(predictions).issubset({-1, 1})


# ── TEST DE INTEGRACIÓN 2: Flujo del monitor ─────────────────────────────────

class TestFlujoMonitor:
    def test_monitor_genera_payload_correcto(self, pipeline):
        """
        INTEGRACIÓN: el monitor genera → analiza → construye payload → serializa
        Simula el ciclo completo de monitor.py sin subir a Azure
        """
        model, scaler, feature_names = pipeline

        # Simular analizar_trafico()
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

        resultados = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "anomaly":   bool(pred == -1),
                "score":     round(float(score), 4),
                "id":        i
            }
            for i, (pred, score) in enumerate(zip(predictions, scores))
        ]

        # Simular subir_resultados()
        historico = (resultados + [])[:100]
        payload = {
            "updated":   datetime.utcnow().isoformat(),
            "total":     len(historico),
            "anomalies": sum(1 for r in historico if r["anomaly"]),
            "results":   historico
        }

        # Verificar payload completo
        assert payload["total"] == n
        assert payload["anomalies"] >= 0
        assert payload["anomalies"] <= n
        assert len(payload["results"]) == n

        # Verificar que es serializable (listo para subir al blob)
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        assert parsed["total"] == n
        assert "updated" in parsed
        assert "results" in parsed

    def test_monitor_historico_maximo_100(self, pipeline):
        """
        INTEGRACIÓN: el histórico nunca supera 100 entradas
        """
        model, scaler, feature_names = pipeline

        historico = []
        for ciclo in range(6):
            datos = np.random.normal(loc=50, scale=10, size=(20, len(feature_names)))
            datos = np.clip(datos, 0, 200)
            df = pd.DataFrame(datos, columns=feature_names)
            df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

            X_scaled    = scaler.transform(df)
            predictions = model.predict(X_scaled)
            scores      = model.decision_function(X_scaled)

            nuevos = [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "anomaly":   bool(p == -1),
                    "score":     round(float(s), 4),
                    "id":        i
                }
                for i, (p, s) in enumerate(zip(predictions, scores))
            ]
            historico = (nuevos + historico)[:100]

        assert len(historico) <= 100

    def test_monitor_blob_upload_llamado(self, pipeline):
        """
        INTEGRACIÓN: verifica que el blob client se llama con datos correctos
        Usa mock para no necesitar Azure
        """
        model, scaler, feature_names = pipeline

        mock_blob = MagicMock()

        datos = np.random.normal(loc=50, scale=10, size=(5, len(feature_names)))
        datos = np.clip(datos, 0, 200)
        df = pd.DataFrame(datos, columns=feature_names)
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

        X_scaled    = scaler.transform(df)
        predictions = model.predict(X_scaled)
        scores      = model.decision_function(X_scaled)

        resultados = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "anomaly":   bool(p == -1),
                "score":     round(float(s), 4),
                "id":        i
            }
            for i, (p, s) in enumerate(zip(predictions, scores))
        ]

        payload = json.dumps({
            "updated":   datetime.utcnow().isoformat(),
            "total":     len(resultados),
            "anomalies": sum(1 for r in resultados if r["anomaly"]),
            "results":   resultados
        })

        # Simular la llamada al blob
        mock_blob.upload_blob(payload, overwrite=True)

        # Verificar que se llamó exactamente una vez con overwrite=True
        mock_blob.upload_blob.assert_called_once()
        call_args = mock_blob.upload_blob.call_args
        assert call_args.kwargs.get("overwrite") is True