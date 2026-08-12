"""
scikit-learn IsolationForest Anomaly Detector.
Fits on baseline healthy telemetry features and detects operational anomalies in real time.
"""

import numpy as np
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest  # type: ignore[import-untyped]

from icop.ml.feature_extractor import ExtractedFeatures


class AnomalyScore(BaseModel):
    service_name: str
    is_anomaly: bool
    anomaly_score: float = Field(..., description="Raw decision score (-0.5 to +0.5)")
    anomaly_confidence: float = Field(..., description="Anomaly percentage 0.0 - 100.0%")


class IsolationForestAnomalyDetector:
    """Uses scikit-learn IsolationForest for unsupervised multi-dimensional anomaly detection."""

    def __init__(self, contamination: float = 0.05) -> None:
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
        )
        self.is_fitted = False
        self._fit_baseline_synthetic()

    def _fit_baseline_synthetic(self) -> None:
        """Pre-fit model on baseline normal operational telemetry distribution."""
        np.random.seed(42)
        # Synthetic baseline: 200 normal samples (CPU ~ 25%, Mem ~ 40%, Latency ~ 20ms, Error ~ 0.01)
        cpus = np.random.normal(25, 5, 200)
        c_z = np.random.normal(0, 1, 200)
        mems = np.random.normal(40, 5, 200)
        m_z = np.random.normal(0, 1, 200)
        lats = np.random.normal(20, 3, 200)
        l_z = np.random.normal(0, 1, 200)
        errs = np.random.normal(0.01, 0.005, 200)
        e_z = np.random.normal(0, 1, 200)

        X_train = np.column_stack([cpus, c_z, mems, m_z, lats, l_z, errs, e_z])
        self.model.fit(X_train)
        self.is_fitted = True

    def predict(self, features: ExtractedFeatures) -> AnomalyScore:
        X = np.array([features.feature_vector])
        raw_score = float(self.model.score_samples(X)[0])  # Lower score -> more anomalous
        prediction = int(self.model.predict(X)[0])  # -1 for anomaly, 1 for normal

        is_anom = prediction == -1
        # Convert decision score to 0-100% confidence percentage
        confidence = float(np.clip((0.5 - raw_score) * 100.0, 0.0, 100.0))

        return AnomalyScore(
            service_name=features.service_name,
            is_anomaly=is_anom,
            anomaly_score=round(raw_score, 4),
            anomaly_confidence=round(confidence, 2),
        )
