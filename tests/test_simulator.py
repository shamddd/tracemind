"""
Unit tests for Incident Simulator and Failure Injection.
"""

from icop.simulator.incident_simulator import FailureMode, IncidentSimulator
from icop.telemetry.collector import TelemetryCollector


def test_incident_simulator_failure_injection() -> None:
    collector = TelemetryCollector()
    simulator = IncidentSimulator(collector)

    # Baseline tick
    points = simulator.tick_simulation()
    assert len(points) == 4

    # Inject CPU_SPIKE on payment-service
    scen = simulator.trigger_incident("payment-service", FailureMode.CPU_SPIKE)
    assert scen.failure_mode == FailureMode.CPU_SPIKE

    anom_points = simulator.tick_simulation()
    pay_point = next(p for p in anom_points if p.service_name == "payment-service")
    assert pay_point.cpu_utilization > 80.0

    simulator.clear_incident("payment-service")
    cleared_points = simulator.tick_simulation()
    cleared_pay = next(p for p in cleared_points if p.service_name == "payment-service")
    assert cleared_pay.cpu_utilization < 50.0
