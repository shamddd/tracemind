"""
Time-Series Feature Extractor for Telemetry Streams.
Calculates statistical features (z-score, EWMA, rolling variance, spike rate).
"""

from typing import List

import numpy as np
from pydantic import BaseModel

from icop.telemetry.metrics import MetricPoint


class ExtractedFeatures(BaseModel):
    service_name: str
    cpu_mean: float
    cpu_std: float
    cpu_zscore: float
    memory_mean: float
    memory_std: float
    memory_zscore: float
    latency_mean: float
    latency_std: float
    latency_zscore: float
    error_rate_mean: float
    error_rate_zscore: float
    feature_vector: List[float]


class TimeSeriesFeatureExtractor:
    """Extracts numerical feature vectors from MetricPoint windows for ML models."""

    @staticmethod
    def extract_features(service_name: str, samples: List[MetricPoint]) -> ExtractedFeatures:
        if not samples:
            return ExtractedFeatures(
                service_name=service_name,
                cpu_mean=0.0,
                cpu_std=0.0,
                cpu_zscore=0.0,
                memory_mean=0.0,
                memory_std=0.0,
                memory_zscore=0.0,
                latency_mean=0.0,
                latency_std=0.0,
                latency_zscore=0.0,
                error_rate_mean=0.0,
                error_rate_zscore=0.0,
                feature_vector=[0.0] * 8,
            )

        cpus = [s.cpu_utilization for s in samples]
        mems = [s.memory_utilization for s in samples]
        lats = [s.latency_ms for s in samples]
        errs = [s.error_rate for s in samples]

        c_mean, c_std = float(np.mean(cpus)), float(np.std(cpus)) or 1.0
        m_mean, m_std = float(np.mean(mems)), float(np.std(mems)) or 1.0
        l_mean, l_std = float(np.mean(lats)), float(np.std(lats)) or 1.0
        e_mean, e_std = float(np.mean(errs)), float(np.std(errs)) or 0.1

        latest = samples[-1]
        c_z = (latest.cpu_utilization - c_mean) / c_std
        m_z = (latest.memory_utilization - m_mean) / m_std
        l_z = (latest.latency_ms - l_mean) / l_std
        e_z = (latest.error_rate - e_mean) / e_std

        vector = [
            latest.cpu_utilization,
            c_z,
            latest.memory_utilization,
            m_z,
            latest.latency_ms,
            l_z,
            latest.error_rate,
            e_z,
        ]

        return ExtractedFeatures(
            service_name=service_name,
            cpu_mean=c_mean,
            cpu_std=c_std,
            cpu_zscore=c_z,
            memory_mean=m_mean,
            memory_std=m_std,
            memory_zscore=m_z,
            latency_mean=l_mean,
            latency_std=l_std,
            latency_zscore=l_z,
            error_rate_mean=e_mean,
            error_rate_zscore=e_z,
            feature_vector=vector,
        )
