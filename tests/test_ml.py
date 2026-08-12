"""
Unit tests for AI Detection & Root Cause Analysis Engine.
"""

from icop.ml.anomaly_detector import IsolationForestAnomalyDetector
from icop.ml.feature_extractor import TimeSeriesFeatureExtractor
from icop.ml.predictor import PredictiveFailureEngine
from icop.ml.rca_engine import RootCauseAnalysisEngine
from icop.telemetry.metrics import MetricPoint


def test_feature_extraction_and_anomaly_detection() -> None:
    samples = [
        MetricPoint(
            service_name="cart-service",
            cpu_utilization=20.0 + i,
            memory_utilization=40.0,
            latency_ms=15.0,
            error_rate=0.01,
        )
        for i in range(10)
    ]

    feats = TimeSeriesFeatureExtractor.extract_features("cart-service", samples)
    assert feats.service_name == "cart-service"
    assert len(feats.feature_vector) == 8

    detector = IsolationForestAnomalyDetector()
    score = detector.predict(feats)
    assert score.service_name == "cart-service"
    assert 0.0 <= score.anomaly_confidence <= 100.0


def test_rca_and_health_scoring() -> None:
    samples = [
        MetricPoint(
            service_name="db-service",
            cpu_utilization=98.0,
            memory_utilization=95.0,
            latency_ms=2500.0,
            error_rate=0.45,
        )
        for _ in range(5)
    ]

    feats = TimeSeriesFeatureExtractor.extract_features("db-service", samples)
    detector = IsolationForestAnomalyDetector()
    score = detector.predict(feats)

    rep = RootCauseAnalysisEngine.analyze_service(feats, score)
    assert rep.service_name == "db-service"
    assert rep.status in ("DEGRADED", "CRITICAL")
    assert len(rep.top_root_cause_metrics) > 0


def test_predictive_failure_forecasting() -> None:
    samples = [
        MetricPoint(
            service_name="api-gateway",
            cpu_utilization=50.0 + (i * 4.0),  # Steep upward trend
            memory_utilization=40.0,
            latency_ms=20.0,
            error_rate=0.01,
        )
        for i in range(10)
    ]

    forecast = PredictiveFailureEngine.forecast_resource_exhaustion("api-gateway", samples, "cpu_utilization")
    assert forecast.service_name == "api-gateway"
    assert forecast.projected_value_5m > 50.0
    assert forecast.predicted_failure_risk in ("HIGH", "SEVERE", "MEDIUM")
