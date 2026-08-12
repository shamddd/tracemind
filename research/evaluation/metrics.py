import numpy as np
from typing import Dict, List, Any

def compute_causalops_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Computes CausalOpsBench metrics:
    - Top1_Accuracy (%): Percentage of incidents where true root cause is ranked #1
    - Top3_Accuracy (%): Percentage of incidents where true root cause is in top 3
    - MRR: Mean Reciprocal Rank (1/Rank)
    - Avg_Latency_ms: Mean diagnosis execution latency
    """
    if not results:
        return {"top1_accuracy": 0.0, "top3_accuracy": 0.0, "mrr": 0.0, "avg_latency_ms": 0.0}

    total = len(results)
    top1_count = sum(1 for r in results if r.get("top_1", False))
    top3_count = sum(1 for r in results if r.get("top_3", False))
    mrrs = [r.get("mrr", 0.0) for r in results]
    latencies = [r.get("diagnosis_latency_ms", 0.0) for r in results]

    return {
        "top1_accuracy": round((top1_count / total) * 100.0, 2),
        "top3_accuracy": round((top3_count / total) * 100.0, 2),
        "mrr": round(float(np.mean(mrrs)), 2),
        "avg_latency_ms": round(float(np.mean(latencies)), 2)
    }
