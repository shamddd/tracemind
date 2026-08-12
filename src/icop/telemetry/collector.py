"""
OpenTelemetry and Prometheus Telemetry Collector & Ingestion Pipeline.
"""

from collections import deque
from typing import Dict, List, Optional

from icop.telemetry.metrics import LogEntry, MetricPoint, ServiceTelemetryWindow, TraceSpan


class TelemetryCollector:
    """Ingests and maintains sliding window telemetry for microservices."""

    def __init__(self, window_size: int = 60) -> None:
        self.window_size = window_size
        self._metrics_buffer: Dict[str, deque[MetricPoint]] = {}
        self._logs_buffer: Dict[str, deque[LogEntry]] = {}
        self._spans_buffer: Dict[str, deque[TraceSpan]] = {}

    def ingest_metric(self, point: MetricPoint) -> None:
        svc = point.service_name
        if svc not in self._metrics_buffer:
            self._metrics_buffer[svc] = deque(maxlen=self.window_size)
        self._metrics_buffer[svc].append(point)

    def ingest_log(self, log: LogEntry) -> None:
        svc = log.service_name
        if svc not in self._logs_buffer:
            self._logs_buffer[svc] = deque(maxlen=200)
        self._logs_buffer[svc].append(log)

    def ingest_span(self, span: TraceSpan) -> None:
        svc = span.service_name
        if svc not in self._spans_buffer:
            self._spans_buffer[svc] = deque(maxlen=200)
        self._spans_buffer[svc].append(span)

    def get_service_window(self, service_name: str) -> ServiceTelemetryWindow:
        samples = list(self._metrics_buffer.get(service_name, deque()))
        logs = list(self._logs_buffer.get(service_name, deque()))
        spans = list(self._spans_buffer.get(service_name, deque()))
        return ServiceTelemetryWindow(
            service_name=service_name,
            samples=samples,
            recent_logs=logs,
            recent_spans=spans,
        )

    def get_all_services(self) -> List[str]:
        return list(self._metrics_buffer.keys())

    def get_latest_metric(self, service_name: str) -> Optional[MetricPoint]:
        buf = self._metrics_buffer.get(service_name)
        if buf and len(buf) > 0:
            return buf[-1]
        return None

    def export_prometheus_metrics(self) -> str:
        """Format metrics in Prometheus text exposition format."""
        lines = []
        lines.append("# HELP service_cpu_utilization CPU utilization percentage")
        lines.append("# TYPE service_cpu_utilization gauge")
        for svc, buf in self._metrics_buffer.items():
            if buf:
                lines.append(f'service_cpu_utilization{{service="{svc}"}} {buf[-1].cpu_utilization}')

        lines.append("# HELP service_memory_utilization Memory utilization percentage")
        lines.append("# TYPE service_memory_utilization gauge")
        for svc, buf in self._metrics_buffer.items():
            if buf:
                lines.append(f'service_memory_utilization{{service="{svc}"}} {buf[-1].memory_utilization}')

        lines.append("# HELP service_latency_ms Request latency in milliseconds")
        lines.append("# TYPE service_latency_ms gauge")
        for svc, buf in self._metrics_buffer.items():
            if buf:
                lines.append(f'service_latency_ms{{service="{svc}"}} {buf[-1].latency_ms}')

        lines.append("# HELP service_error_rate Error rate ratio")
        lines.append("# TYPE service_error_rate gauge")
        for svc, buf in self._metrics_buffer.items():
            if buf:
                lines.append(f'service_error_rate{{service="{svc}"}} {buf[-1].error_rate}')

        return "\n".join(lines) + "\n"
