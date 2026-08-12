"""
FastAPI Route handlers for Observability Platform API.
"""

from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect, status

from icop.agent.agent import IncidentReport, ReliabilityAgent
from icop.api.schemas import (
    DiagnoseServiceRequest,
    HealthCheckResponse,
    TriggerIncidentRequest,
)
from icop.api.websocket import ws_manager
from icop.ml.anomaly_detector import IsolationForestAnomalyDetector
from icop.ml.feature_extractor import TimeSeriesFeatureExtractor
from icop.ml.rca_engine import ClusterRCAReport, RootCauseAnalysisEngine, ServiceHealthReport
from icop.simulator.incident_simulator import IncidentSimulator, SimulationScenario
from icop.telemetry.collector import TelemetryCollector

router = APIRouter()

collector = TelemetryCollector()
simulator = IncidentSimulator(collector)
anomaly_detector = IsolationForestAnomalyDetector()
agent = ReliabilityAgent(collector)

# Initialize baseline simulation data
simulator.tick_simulation()


@router.get("/health", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    services = simulator.DEFAULT_SERVICES
    reports: list[ServiceHealthReport] = []
    for svc in services:
        window = collector.get_service_window(svc)
        feats = TimeSeriesFeatureExtractor.extract_features(svc, window.samples)
        anom = anomaly_detector.predict(feats)
        rep = RootCauseAnalysisEngine.analyze_service(feats, anom)
        reports.append(rep)

    cluster_rca = RootCauseAnalysisEngine.analyze_cluster(reports)
    return HealthCheckResponse(
        status="HEALTHY" if cluster_rca.overall_cluster_health >= 70.0 else "DEGRADED",
        cluster_health_score=cluster_rca.overall_cluster_health,
        services_monitored=len(services),
    )


@router.get("/metrics")
def prometheus_metrics() -> Response:
    content = collector.export_prometheus_metrics()
    return Response(content=content, media_type="text/plain")


@router.post("/incidents/simulate", response_model=SimulationScenario, status_code=status.HTTP_201_CREATED)
def trigger_incident(body: TriggerIncidentRequest) -> SimulationScenario:
    scen = simulator.trigger_incident(body.service_name, body.failure_mode, body.duration_seconds)
    simulator.tick_simulation()
    return scen


@router.delete("/incidents/simulate/{service_name}")
def clear_incident(service_name: str) -> dict[str, str]:
    simulator.clear_incident(service_name)
    return {"message": f"Cleared incident simulation for service '{service_name}'"}


@router.get("/analysis/rca", response_model=ClusterRCAReport)
def get_cluster_rca() -> ClusterRCAReport:
    simulator.tick_simulation()
    services = simulator.DEFAULT_SERVICES
    reports: list[ServiceHealthReport] = []
    for svc in services:
        window = collector.get_service_window(svc)
        feats = TimeSeriesFeatureExtractor.extract_features(svc, window.samples)
        anom = anomaly_detector.predict(feats)
        rep = RootCauseAnalysisEngine.analyze_service(feats, anom)
        reports.append(rep)

    return RootCauseAnalysisEngine.analyze_cluster(reports)


@router.post("/agent/diagnose", response_model=IncidentReport)
def diagnose_service(body: DiagnoseServiceRequest) -> IncidentReport:
    return agent.diagnose_service(body.service_name)


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            # Send latest telemetry tick over WS
            points = simulator.tick_simulation()
            data = [p.model_dump() for p in points]
            await ws_manager.broadcast({"type": "TELEMETRY_TICK", "points": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
