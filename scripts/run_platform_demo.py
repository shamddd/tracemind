#!/usr/bin/env python3
"""
Full Platform Demo Script.
Starts FastAPI server in background or runs telemetry collector tick cycle.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from icop.api.routes import collector, simulator
from icop.simulator.incident_simulator import FailureMode


def main() -> None:
    print("Executing Intelligent Cloud Observability Platform Demonstration...")
    points = simulator.tick_simulation()
    print(f"Generated telemetry tick for {len(points)} microservices.")

    # Trigger sample incident
    simulator.trigger_incident("payment-service", FailureMode.CPU_SPIKE)
    points_anom = simulator.tick_simulation()
    print(f"Triggered CPU_SPIKE on payment-service. Ingested {len(points_anom)} metric points.")

    prom_export = collector.export_prometheus_metrics()
    print("\nSample Prometheus Exposition Format:\n")
    print("\n".join(prom_export.splitlines()[:12]))
    print("\nPlatform demo finished successfully.")


if __name__ == "__main__":
    main()
