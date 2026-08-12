"""
Integration tests for FastAPI Observability Platform Control Plane.
"""

from fastapi.testclient import TestClient

from icop.api.app import app

client = TestClient(app)


def test_api_health_and_metrics() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("HEALTHY", "DEGRADED")

    prom_resp = client.get("/api/v1/metrics")
    assert prom_resp.status_code == 200
    assert "service_cpu_utilization" in prom_resp.text


def test_api_incident_simulation_and_rca() -> None:
    # Trigger incident via API
    req = {
        "service_name": "payment-service",
        "failure_mode": "CPU_SPIKE",
        "duration_seconds": 60,
    }
    sim_resp = client.post("/api/v1/incidents/simulate", json=req)
    assert sim_resp.status_code == 201

    # Fetch Cluster RCA
    rca_resp = client.get("/api/v1/analysis/rca")
    assert rca_resp.status_code == 200
    assert len(rca_resp.json()["ranked_suspect_services"]) > 0

    # Agent Diagnosis
    diag_resp = client.post("/api/v1/agent/diagnose", json={"service_name": "payment-service"})
    assert diag_resp.status_code == 200
    assert diag_resp.json()["target_service"] == "payment-service"

    # Clear incident
    clear_resp = client.delete("/api/v1/incidents/simulate/payment-service")
    assert clear_resp.status_code == 200
