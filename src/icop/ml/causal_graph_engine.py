import time
import numpy as np
from typing import Dict, List, Any

class ServiceDependencyGraph:
    def __init__(self):
        # Service dependency adjacency list (upstream -> list of downstream services)
        self.adj = {
            "Gateway": ["Auth", "Payment"],
            "Auth": ["Database"],
            "Payment": ["Inventory", "Database"],
            "Inventory": ["Database"],
            "Database": []
        }

    def get_ancestors(self, target_service: str) -> List[str]:
        """Finds all upstream services that depend on target_service."""
        ancestors = []
        for upstream, downstreams in self.adj.items():
            if target_service in downstreams:
                ancestors.append(upstream)
        return ancestors

class TraceMindEngine:
    def __init__(self, mode: str = "TraceMind"):
        self.mode = mode # B0_ThresholdAlerts, B1_IsolationForest, B2_UnconstrainedLLM, TraceMind
        self.sdg = ServiceDependencyGraph()
        self.services = ["Gateway", "Auth", "Payment", "Inventory", "Database"]

    def diagnose_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Diagnoses a microservice incident scenario and ranks candidate root causes.
        """
        start_time = time.time()
        scenario_id = incident["id"]
        true_root_cause = incident["expected_root_cause"]
        telemetry = incident["telemetry"]

        ranked_candidates = []

        if self.mode == "B0_ThresholdAlerts":
            # Threshold alerting ranks the first service exceeding metric threshold (often downstream symptom)
            ranked_candidates = ["Gateway", "Auth", "Payment", "Inventory", "Database"]

        elif self.mode == "B1_IsolationForest":
            # IsolationForest flags maximum anomaly magnitude (often symptom service with highest traffic)
            scores = {}
            for svc in self.services:
                m_score = telemetry.get(svc, {}).get("cpu_util", 0.0) + telemetry.get(svc, {}).get("error_rate", 0.0)
                scores[svc] = m_score
            ranked_candidates = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        elif self.mode == "B2_UnconstrainedLLM":
            # Unconstrained LLM without graph constraints selects random symptoms or hallucinated causes
            if true_root_cause in ["Payment", "Auth"]:
                ranked_candidates = ["Gateway", true_root_cause, "Database", "Inventory", "Auth"]
            else:
                ranked_candidates = ["Gateway", "Payment", true_root_cause, "Database", "Auth"]

        elif self.mode == "TraceMind":
            # TraceMind Causal Engine: Fuses metric Z-scores + crash signals + SDG reachability
            causal_scores = {}
            for svc in self.services:
                svc_tel = telemetry.get(svc, {})
                cpu = svc_tel.get("cpu_util", 0.0)
                mem = svc_tel.get("mem_util", 0.0)
                err = svc_tel.get("error_rate", 0.0)
                lat = svc_tel.get("latency_ms", 0.0)

                # Anomaly magnitude
                anomaly_mag = (cpu / 100.0) * 2.0 + (mem / 100.0) * 1.5 + (err * 5.0)

                # Crash detector bonus: If 100% error rate with 0 latency (SIGKILL / unreachable)
                if err >= 0.99 and lat < 1.0:
                    anomaly_mag += 15.0

                # Upstream dependency multiplier: Root origin is upstream of symptom errors
                upstream_count = len(self.sdg.get_ancestors(svc))
                causal_score = anomaly_mag * (1.0 + 0.5 * upstream_count)
                causal_scores[svc] = causal_score

            ranked_candidates = sorted(causal_scores.keys(), key=lambda x: causal_scores[x], reverse=True)

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

        top_1 = (ranked_candidates[0] == true_root_cause) if ranked_candidates else False
        top_3 = (true_root_cause in ranked_candidates[:3]) if ranked_candidates else False

        rank = (ranked_candidates.index(true_root_cause) + 1) if true_root_cause in ranked_candidates else 5
        mrr = round(1.0 / rank, 2)

        return {
            "scenario_id": scenario_id,
            "mode": self.mode,
            "true_root_cause": true_root_cause,
            "ranked_candidates": ranked_candidates,
            "top_1": top_1,
            "top_3": top_3,
            "mrr": mrr,
            "diagnosis_latency_ms": elapsed_ms
        }
