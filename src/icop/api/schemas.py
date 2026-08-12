"""
API Request and Response schemas for Observability Platform Control Plane.
"""

from typing import Optional

from pydantic import BaseModel

from icop.ml.predictor import PredictiveForecast
from icop.ml.rca_engine import ServiceHealthReport
from icop.simulator.incident_simulator import FailureMode
from icop.telemetry.metrics import MetricPoint


class TriggerIncidentRequest(BaseModel):
    service_name: str
    failure_mode: FailureMode
    duration_seconds: int = 60


class HealthCheckResponse(BaseModel):
    status: str = "HEALTHY"
    cluster_health_score: float
    services_monitored: int


class ServiceMetricsResponse(BaseModel):
    service_name: str
    latest_sample: Optional[MetricPoint] = None
    health_report: ServiceHealthReport
    predictive_forecast: PredictiveForecast


class DiagnoseServiceRequest(BaseModel):
    service_name: str
