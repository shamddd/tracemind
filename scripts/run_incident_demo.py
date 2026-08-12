#!/usr/bin/env python3
"""
Interactive Incident Simulation and AI Diagnosis Demo Script.
Demonstrates live failure injection, IsolationForest anomaly detection,
Root Cause Analysis, and AI Reliability Agent diagnosis.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from icop.agent.agent import ReliabilityAgent
from icop.ml.anomaly_detector import IsolationForestAnomalyDetector
from icop.ml.feature_extractor import TimeSeriesFeatureExtractor
from icop.ml.predictor import PredictiveFailureEngine
from icop.ml.rca_engine import RootCauseAnalysisEngine
from icop.simulator.incident_simulator import FailureMode, IncidentSimulator
from icop.telemetry.collector import TelemetryCollector


def main() -> None:
    print("=" * 70)
    print("  INTELLIGENT CLOUD OBSERVABILITY PLATFORM — INCIDENT DEMO")
    print("=" * 70)

    collector = TelemetryCollector()
    simulator = IncidentSimulator(collector)
    detector = IsolationForestAnomalyDetector()
    agent = ReliabilityAgent(collector)

    print("\n[Step 1] Initializing Healthy Telemetry Baseline for 4 Microservices...")
    for _ in range(10):
        simulator.tick_simulation()

    # Check baseline health
    reports = []
    for svc in simulator.DEFAULT_SERVICES:
        w = collector.get_service_window(svc)
        feats = TimeSeriesFeatureExtractor.extract_features(svc, w.samples)
        anom = detector.predict(feats)
        rep = RootCauseAnalysisEngine.analyze_service(feats, anom)
        reports.append(rep)

    cluster_rca = RootCauseAnalysisEngine.analyze_cluster(reports)
    print(f"  Cluster Health Score: {cluster_rca.overall_cluster_health}/100.0 (Status: HEALTHY)")

    # Inject Failure Mode 1: CPU Spike on payment-service
    print("\n[Step 2] Injecting Incident Scenario: CPU_SPIKE on 'payment-service'...")
    simulator.trigger_incident("payment-service", FailureMode.CPU_SPIKE, duration_sec=60)
    for _ in range(5):
        simulator.tick_simulation()

    w_pay = collector.get_service_window("payment-service")
    feats_pay = TimeSeriesFeatureExtractor.extract_features("payment-service", w_pay.samples)
    anom_pay = detector.predict(feats_pay)
    rep_pay = RootCauseAnalysisEngine.analyze_service(feats_pay, anom_pay)

    print(f"  IsolationForest Anomaly Score: {anom_pay.anomaly_score} (Confidence: {anom_pay.anomaly_confidence}%)")
    print(f"  Service Health Status: {rep_pay.status} ({rep_pay.health_score}/100.0)")
    if rep_pay.top_root_cause_metrics:
        top_m = rep_pay.top_root_cause_metrics[0]
        print(f"  Root Cause Metric: {top_m.metric_name} (Z: {top_m.zscore}, Share: {top_m.contribution_score}%)")

    # Inject Failure Mode 2: LATENCY_INCREASE & DATABASE_SLOWDOWN on auth-service
    print("\n[Step 3] Injecting Incident Scenario: DATABASE_SLOWDOWN on 'auth-service'...")
    simulator.trigger_incident("auth-service", FailureMode.DATABASE_SLOWDOWN, duration_sec=60)
    for _ in range(5):
        simulator.tick_simulation()

    w_auth = collector.get_service_window("auth-service")
    forecast_auth = PredictiveFailureEngine.forecast_resource_exhaustion("auth-service", w_auth.samples, "latency_ms")
    print(f"  Predictive SLA Failure Risk: {forecast_auth.predicted_failure_risk}")
    print(f"  Current Latency: {forecast_auth.current_value} ms -> Projected 5m: {forecast_auth.projected_value_5m} ms")

    # Invoke AI Infrastructure Reliability Agent
    print("\n[Step 4] Invoking Autonomous AI Reliability Agent for Incident Diagnosis...")
    report = agent.diagnose_service("payment-service")
    print(report.markdown_report)

    print("Incident Simulation & AI Diagnosis Demo Completed Successfully!")


if __name__ == "__main__":
    main()
