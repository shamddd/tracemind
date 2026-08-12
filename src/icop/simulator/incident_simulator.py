"""
Incident Simulation System for Operational Chaos Testing & Failure Injection.
Generates realistic telemetry streams for microservices under healthy and degraded states.
"""

import random
import time
from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field

from icop.telemetry.collector import TelemetryCollector
from icop.telemetry.metrics import LogEntry, MetricPoint, TraceSpan


class FailureMode(str, Enum):
    NONE = "NONE"
    CPU_SPIKE = "CPU_SPIKE"
    MEMORY_SPIKE = "MEMORY_SPIKE"
    LATENCY_INCREASE = "LATENCY_INCREASE"
    SERVICE_CRASH = "SERVICE_CRASH"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    DATABASE_SLOWDOWN = "DATABASE_SLOWDOWN"


class SimulationScenario(BaseModel):
    service_name: str
    failure_mode: FailureMode
    duration_seconds: int = 60
    started_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))


class IncidentSimulator:
    """Simulates multi-microservice cluster telemetry and injects failure scenarios."""

    DEFAULT_SERVICES = ["auth-service", "payment-service", "inventory-service", "gateway-api"]

    def __init__(self, collector: TelemetryCollector) -> None:
        self.collector = collector
        self.active_scenarios: Dict[str, SimulationScenario] = {}

    def trigger_incident(
        self, service_name: str, failure_mode: FailureMode, duration_sec: int = 60
    ) -> SimulationScenario:
        scen = SimulationScenario(
            service_name=service_name,
            failure_mode=failure_mode,
            duration_seconds=duration_sec,
        )
        self.active_scenarios[service_name] = scen
        return scen

    def clear_incident(self, service_name: str) -> None:
        self.active_scenarios.pop(service_name, None)

    def tick_simulation(self) -> List[MetricPoint]:
        """Generates 1 tick of telemetry for all microservices."""
        now_ms = int(time.time() * 1000)
        generated_points: List[MetricPoint] = []

        for svc in self.DEFAULT_SERVICES:
            scen = self.active_scenarios.get(svc)

            # Baseline normal operational metrics
            cpu = random.uniform(15.0, 30.0)
            mem = random.uniform(35.0, 50.0)
            lat = random.uniform(15.0, 25.0)
            err = random.uniform(0.001, 0.01)
            reqs = random.randint(150, 300)
            db_conns = random.randint(15, 30)

            if scen and (now_ms - scen.started_at_ms) < (scen.duration_seconds * 1000):
                # Apply failure injection modifications
                if scen.failure_mode == FailureMode.CPU_SPIKE:
                    cpu = random.uniform(92.0, 99.8)
                elif scen.failure_mode == FailureMode.MEMORY_SPIKE:
                    mem = random.uniform(88.0, 98.5)
                elif scen.failure_mode == FailureMode.LATENCY_INCREASE:
                    lat = random.uniform(850.0, 2500.0)
                elif scen.failure_mode == FailureMode.SERVICE_CRASH:
                    err = random.uniform(0.85, 1.0)
                    lat = random.uniform(5000.0, 10000.0)
                    reqs = random.randint(0, 10)
                elif scen.failure_mode == FailureMode.DEPENDENCY_FAILURE:
                    err = random.uniform(0.40, 0.75)
                    lat = random.uniform(1200.0, 3500.0)
                elif scen.failure_mode == FailureMode.DATABASE_SLOWDOWN:
                    lat = random.uniform(1500.0, 4500.0)
                    db_conns = random.randint(95, 100)

                # Generate structured error log
                self.collector.ingest_log(
                    LogEntry(
                        service_name=svc,
                        level="ERROR",
                        message=f"Fault injection active [{scen.failure_mode.value}]: metric threshold exceeded",
                        trace_id=f"trace-{now_ms}",
                        attributes={"failure_mode": scen.failure_mode.value},
                    )
                )

            point = MetricPoint(
                service_name=svc,
                timestamp_ms=now_ms,
                cpu_utilization=round(cpu, 2),
                memory_utilization=round(mem, 2),
                latency_ms=round(lat, 2),
                error_rate=round(err, 4),
                request_count=reqs,
                db_connections=db_conns,
            )

            self.collector.ingest_metric(point)
            self.collector.ingest_span(
                TraceSpan(
                    trace_id=f"t-{now_ms}-{svc}",
                    span_id=f"s-{now_ms}",
                    service_name=svc,
                    operation_name="HTTP GET /api/process",
                    duration_ms=round(lat, 2),
                    status_code="ERROR" if err > 0.1 else "OK",
                )
            )
            generated_points.append(point)

        return generated_points
