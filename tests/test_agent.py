"""
Unit tests for AI Infrastructure Reliability Agent.
"""

from icop.agent.agent import ReliabilityAgent
from icop.simulator.incident_simulator import FailureMode, IncidentSimulator
from icop.telemetry.collector import TelemetryCollector


def test_reliability_agent_diagnosis() -> None:
    collector = TelemetryCollector()
    simulator = IncidentSimulator(collector)
    agent = ReliabilityAgent(collector)

    simulator.trigger_incident("auth-service", FailureMode.LATENCY_INCREASE)
    for _ in range(5):
        simulator.tick_simulation()

    report = agent.diagnose_service("auth-service")
    assert report.target_service == "auth-service"
    assert report.severity in ("WARNING", "CRITICAL", "INFO")
    assert len(report.hypotheses_ranked) > 0
    assert "Incident Diagnosis Report" in report.markdown_report
