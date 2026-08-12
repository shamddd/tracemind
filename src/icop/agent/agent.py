"""
AI Infrastructure Reliability Agent.
Observes anomalies, correlates telemetry across metrics/logs/spans, forms hypotheses, and produces incident reports.
"""

import uuid
from typing import List

from pydantic import BaseModel

from icop.agent.tools import AgentInspectionTools, RemediationProposal
from icop.ml.anomaly_detector import IsolationForestAnomalyDetector
from icop.ml.feature_extractor import TimeSeriesFeatureExtractor
from icop.ml.predictor import PredictiveFailureEngine
from icop.ml.rca_engine import RootCauseAnalysisEngine, ServiceHealthReport
from icop.telemetry.collector import TelemetryCollector


class IncidentReport(BaseModel):
    incident_id: str
    target_service: str
    severity: str
    root_cause_summary: str
    observed_anomalies: List[str]
    evidence_logs: List[str]
    evidence_spans: List[str]
    hypotheses_ranked: List[str]
    recommended_remediations: List[RemediationProposal]
    markdown_report: str


class ReliabilityAgent:
    """Autonomous AI Reliability Agent for cloud incident diagnosis and remediation planning."""

    def __init__(self, collector: TelemetryCollector) -> None:
        self.collector = collector
        self.tools = AgentInspectionTools(collector)
        self.anomaly_detector = IsolationForestAnomalyDetector()
        self.feature_extractor = TimeSeriesFeatureExtractor()

    def diagnose_service(self, service_name: str) -> IncidentReport:
        window = self.tools.inspect_service(service_name)
        features = self.feature_extractor.extract_features(service_name, window.samples)
        anomaly = self.anomaly_detector.predict(features)
        health_report: ServiceHealthReport = RootCauseAnalysisEngine.analyze_service(features, anomaly)
        _ = PredictiveFailureEngine.forecast_resource_exhaustion(service_name, window.samples)

        # Query evidence logs and spans
        error_logs = self.tools.query_error_logs(service_name)
        slow_spans = self.tools.inspect_spans(service_name)

        log_snippets = [f"[{log_item.level}] {log_item.message}" for log_item in error_logs[:3]]
        span_snippets = [f"[{s.operation_name}] {s.duration_ms}ms ({s.status_code})" for s in slow_spans[:3]]

        # Formulate hypotheses
        hypotheses: List[str] = []
        for attr in health_report.top_root_cause_metrics:
            if attr.metric_name == "CPU_UTILIZATION":
                hypotheses.append(
                    "Hypothesis 1 (High Confidence): CPU saturation caused by inefficient process loop"
                )
            elif attr.metric_name == "MEMORY_UTILIZATION":
                hypotheses.append(
                    "Hypothesis 1 (High Confidence): Memory leak or uncollected cache objects exhausting heap space"
                )
            elif attr.metric_name == "LATENCY_MS":
                hypotheses.append(
                    "Hypothesis 1 (High Confidence): Upstream API dependency blocking or downstream database lock"
                )
            elif attr.metric_name == "ERROR_RATE":
                hypotheses.append(
                    "Hypothesis 1 (High Confidence): Unhandled exception / crash in service request handler"
                )

        if not hypotheses:
            hypotheses.append("Hypothesis 1: Transient network jitter or metric reporting noise")

        # Propose safe remediation actions
        remediations: List[RemediationProposal] = []
        if health_report.status != "HEALTHY":
            remediations.append(
                self.tools.propose_remediation_action(
                    service_name,
                    action=f"Scale out horizontal pod count for service {service_name}",
                    impact="Increases cluster compute capacity to absorb workload load",
                )
            )
            remediations.append(
                self.tools.propose_remediation_action(
                    service_name,
                    action=f"Restart pod instances for {service_name}",
                    impact="Flushes corrupted memory state or leaked process handles",
                )
            )

        inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        severity = (
            "CRITICAL"
            if health_report.status == "CRITICAL"
            else ("WARNING" if health_report.status == "DEGRADED" else "INFO")
        )
        top_metric = (
            health_report.top_root_cause_metrics[0].metric_name
            if health_report.top_root_cause_metrics
            else "N/A"
        )
        summary = f"{health_report.status} state on {service_name}: top contributor {top_metric}"

        md_report = f"""# Incident Diagnosis Report: {inc_id}
**Target Service**: `{service_name}`  
**Severity**: `{severity}`  
**Health Score**: `{health_report.health_score}/100.0` ({health_report.status})  
**Anomaly Confidence**: `{anomaly.anomaly_confidence}%`  

## Root Cause Summary
{summary}

## Diagnostic Hypotheses
"""
        for h in hypotheses:
            md_report += f"- {h}\n"

        md_report += "\n## Evidence & Telemetry Logs\n"
        for log in log_snippets:
            md_report += f"- `{log}`\n"

        md_report += "\n## Recommended Remediations (Human Approval Required)\n"
        for rem in remediations:
            md_report += f"- **[{rem.remediation_id}]** {rem.proposed_action} *(Impact: {rem.impact_assessment})*\n"

        return IncidentReport(
            incident_id=inc_id,
            target_service=service_name,
            severity=severity,
            root_cause_summary=summary,
            observed_anomalies=[a.metric_name for a in health_report.top_root_cause_metrics],
            evidence_logs=log_snippets,
            evidence_spans=span_snippets,
            hypotheses_ranked=hypotheses,
            recommended_remediations=remediations,
            markdown_report=md_report,
        )
