"""
Predictive Failure Engine.
Uses linear slope trend extrapolation to predict time-to-resource-exhaustion or SLA breach.
"""

from typing import List, Optional

import numpy as np
from pydantic import BaseModel, Field

from icop.telemetry.metrics import MetricPoint


class PredictiveForecast(BaseModel):
    service_name: str
    target_metric: str
    current_value: float
    projected_value_5m: float
    time_to_exhaustion_sec: Optional[float] = Field(
        default=None, description="Seconds until 100% threshold breach"
    )
    predicted_failure_risk: str = Field(
        default="LOW", description="LOW, MEDIUM, HIGH, or SEVERE"
    )


class PredictiveFailureEngine:
    """Extrapolates metric trajectory slopes to predict resource exhaustion before SLA breach."""

    @staticmethod
    def forecast_resource_exhaustion(
        service_name: str, samples: List[MetricPoint], metric_attr: str = "cpu_utilization"
    ) -> PredictiveForecast:
        if len(samples) < 5:
            val = getattr(samples[-1], metric_attr) if samples else 0.0
            return PredictiveForecast(
                service_name=service_name,
                target_metric=metric_attr,
                current_value=val,
                projected_value_5m=val,
                time_to_exhaustion_sec=None,
                predicted_failure_risk="LOW",
            )

        y = np.array([getattr(s, metric_attr) for s in samples])
        x = np.arange(len(y))

        # Linear regression slope fitting (dy/dx)
        slope, intercept = np.polyfit(x, y, 1)
        current_val = float(y[-1])

        # Project 5 minutes ahead (assuming 1 sample = 5 sec)
        projected_5m = float(np.clip(current_val + (slope * 60), 0.0, 100.0))

        time_to_exhaustion: Optional[float] = None
        risk = "LOW"

        if slope > 0.1:  # Positive upward trend
            rem_headroom = 100.0 - current_val
            steps_needed = rem_headroom / slope if slope > 0 else 9999
            time_to_exhaustion = float(steps_needed * 5.0)  # Convert steps to seconds

            if time_to_exhaustion < 120 or current_val > 85.0:
                risk = "SEVERE"
            elif time_to_exhaustion < 300 or current_val > 70.0:
                risk = "HIGH"
            elif time_to_exhaustion < 600:
                risk = "MEDIUM"

        return PredictiveForecast(
            service_name=service_name,
            target_metric=metric_attr,
            current_value=round(current_val, 2),
            projected_value_5m=round(projected_5m, 2),
            time_to_exhaustion_sec=(
                round(time_to_exhaustion, 1) if time_to_exhaustion is not None else None
            ),
            predicted_failure_risk=risk,
        )
