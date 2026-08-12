"""
Telemetry data models for OpenTelemetry metrics, logs, and trace spans.
"""

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetricPoint(BaseModel):
    service_name: str
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    cpu_utilization: float = Field(..., description="CPU percentage 0.0 - 100.0")
    memory_utilization: float = Field(..., description="Memory percentage 0.0 - 100.0")
    latency_ms: float = Field(..., description="Request latency in ms")
    error_rate: float = Field(..., description="Error rate ratio 0.0 - 1.0")
    request_count: int = Field(default=100, description="Requests processed in window")
    db_connections: int = Field(default=20, description="Active DB connections")


class LogEntry(BaseModel):
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    service_name: str
    level: str = "INFO"
    message: str
    trace_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service_name: str
    operation_name: str
    duration_ms: float
    status_code: str = "OK"
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ServiceTelemetryWindow(BaseModel):
    service_name: str
    samples: List[MetricPoint] = Field(default_factory=list)
    recent_logs: List[LogEntry] = Field(default_factory=list)
    recent_spans: List[TraceSpan] = Field(default_factory=list)
