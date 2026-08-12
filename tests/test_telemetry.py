"""
Unit tests for Telemetry Collector and metrics processing.
"""

from icop.telemetry.collector import TelemetryCollector
from icop.telemetry.metrics import LogEntry, MetricPoint, TraceSpan


def test_telemetry_collector_ingestion() -> None:
    collector = TelemetryCollector(window_size=10)
    point = MetricPoint(
        service_name="auth-service",
        cpu_utilization=45.0,
        memory_utilization=60.0,
        latency_ms=25.0,
        error_rate=0.02,
    )
    collector.ingest_metric(point)

    log = LogEntry(service_name="auth-service", level="INFO", message="Login success")
    collector.ingest_log(log)

    span = TraceSpan(
        trace_id="t1",
        span_id="s1",
        service_name="auth-service",
        operation_name="GET /login",
        duration_ms=25.0,
    )
    collector.ingest_span(span)

    window = collector.get_service_window("auth-service")
    assert len(window.samples) == 1
    assert len(window.recent_logs) == 1
    assert len(window.recent_spans) == 1

    latest = collector.get_latest_metric("auth-service")
    assert latest is not None
    assert latest.cpu_utilization == 45.0


def test_prometheus_exposition_export() -> None:
    collector = TelemetryCollector()
    point = MetricPoint(
        service_name="payment-service",
        cpu_utilization=55.5,
        memory_utilization=70.0,
        latency_ms=120.0,
        error_rate=0.01,
    )
    collector.ingest_metric(point)

    export = collector.export_prometheus_metrics()
    assert "service_cpu_utilization" in export
    assert 'service="payment-service"' in export
    assert "55.5" in export
