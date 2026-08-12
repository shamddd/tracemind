"""
Controlled Inspection Tools for AI Infrastructure Reliability Agent.
Safety Guard: Read-only inspection and proposal functions. NO autonomous destructive changes.
"""

from typing import List

from pydantic import BaseModel

from icop.telemetry.collector import TelemetryCollector
from icop.telemetry.metrics import LogEntry, ServiceTelemetryWindow, TraceSpan


class RemediationProposal(BaseModel):
    remediation_id: str
    target_service: str
    proposed_action: str
    impact_assessment: str
    requires_human_approval: bool = True
    approved: bool = False


class AgentInspectionTools:
    """Safe read-only telemetry inspection tools for AI Reliability Agent."""

    def __init__(self, collector: TelemetryCollector) -> None:
        self.collector = collector

    def inspect_service(self, service_name: str) -> ServiceTelemetryWindow:
        return self.collector.get_service_window(service_name)

    def query_error_logs(self, service_name: str) -> List[LogEntry]:
        window = self.collector.get_service_window(service_name)
        return [log for log in window.recent_logs if log.level in ("ERROR", "WARN", "CRITICAL")]

    def inspect_spans(self, service_name: str) -> List[TraceSpan]:
        window = self.collector.get_service_window(service_name)
        return [span for span in window.recent_spans if span.status_code == "ERROR" or span.duration_ms > 1000.0]

    def propose_remediation_action(
        self, service_name: str, action: str, impact: str
    ) -> RemediationProposal:
        import uuid

        rem_id = f"rem-{uuid.uuid4().hex[:8]}"
        return RemediationProposal(
            remediation_id=rem_id,
            target_service=service_name,
            proposed_action=action,
            impact_assessment=impact,
            requires_human_approval=True,
            approved=False,
        )
