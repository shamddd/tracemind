"""
Automated Root-Cause Analysis (RCA) and Service Health Scoring Engine.
Calculates metric feature attributions, health scores (0-100), and ranks suspect root causes.
"""

from typing import Dict, List

from pydantic import BaseModel, Field

from icop.ml.anomaly_detector import AnomalyScore
from icop.ml.feature_extractor import ExtractedFeatures


class SuspectMetricAttribution(BaseModel):
    metric_name: str
    zscore: float
    contribution_score: float


class ServiceHealthReport(BaseModel):
    service_name: str
    health_score: float = Field(..., description="Service health 0.0 (CRITICAL) to 100.0 (HEALTHY)")
    status: str = Field(..., description="HEALTHY, DEGRADED, or CRITICAL")
    is_anomaly: bool
    top_root_cause_metrics: List[SuspectMetricAttribution] = Field(default_factory=list)


class ClusterRCAReport(BaseModel):
    overall_cluster_health: float
    ranked_suspect_services: List[ServiceHealthReport]


class RootCauseAnalysisEngine:
    """Ranks suspect microservices and feature attributions during operational incidents."""

    NORMAL_BASELINES = {
        "CPU_UTILIZATION": (25.0, 5.0),
        "MEMORY_UTILIZATION": (40.0, 5.0),
        "LATENCY_MS": (25.0, 10.0),
        "ERROR_RATE": (0.01, 0.01),
    }

    @classmethod
    def analyze_service(cls, features: ExtractedFeatures, anomaly: AnomalyScore) -> ServiceHealthReport:
        attributions: List[SuspectMetricAttribution] = []

        metrics_val_map = {
            "CPU_UTILIZATION": features.feature_vector[0],
            "MEMORY_UTILIZATION": features.feature_vector[2],
            "LATENCY_MS": features.feature_vector[4],
            "ERROR_RATE": features.feature_vector[6],
        }

        z_scores: Dict[str, float] = {}
        for m_name, val in metrics_val_map.items():
            base_mean, base_std = cls.NORMAL_BASELINES[m_name]
            z = abs((val - base_mean) / base_std)
            z_scores[m_name] = z

        total_z = sum(z_scores.values()) or 1.0

        for m_name, z in z_scores.items():
            contrib = (z / total_z) * 100.0
            if z > 1.2:  # Deviates significantly from normal baseline
                attributions.append(
                    SuspectMetricAttribution(
                        metric_name=m_name,
                        zscore=round(z, 2),
                        contribution_score=round(contrib, 2),
                    )
                )

        attributions.sort(key=lambda x: x.contribution_score, reverse=True)

        max_z = max(z_scores.values(), default=0.0)
        base_health = max(0.0, 100.0 - (max_z * 8.0) - (anomaly.anomaly_confidence * 0.3))
        health_score = round(base_health, 1)

        if health_score >= 80.0:
            svc_status = "HEALTHY"
        elif health_score >= 50.0:
            svc_status = "DEGRADED"
        else:
            svc_status = "CRITICAL"

        return ServiceHealthReport(
            service_name=features.service_name,
            health_score=health_score,
            status=svc_status,
            is_anomaly=anomaly.is_anomaly or (health_score < 75.0),
            top_root_cause_metrics=attributions,
        )

    @classmethod
    def analyze_cluster(cls, service_reports: List[ServiceHealthReport]) -> ClusterRCAReport:
        if not service_reports:
            return ClusterRCAReport(overall_cluster_health=100.0, ranked_suspect_services=[])

        avg_health = float(sum(r.health_score for r in service_reports) / len(service_reports))
        ranked = sorted(service_reports, key=lambda x: x.health_score)

        return ClusterRCAReport(
            overall_cluster_health=round(avg_health, 1),
            ranked_suspect_services=ranked,
        )
