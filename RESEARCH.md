# TraceMind: Graph-Constrained Causal Reasoning for Microservice RCA

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Manuscript](https://img.shields.io/badge/Manuscript-In_Preparation-orange.svg)](research/paper/main.tex)

> **Official Research Artifact**: Graph-Constrained Causal Evidence Attribution and Multi-Modal Telemetry Fusion for Microservice Systems.

---

## Executive Overview

- **Author**: Sham Satish Thakare (`151498087+shamddd@users.noreply.github.com`)
- **Primary Research Question**: *"Does graph-constrained causal reasoning over multi-modal telemetry improve root-cause localization accuracy in cascading microservice failures?"*
- **Primary Contribution**: **TraceMind**, a causal graph engine fusing OpenTelemetry metrics, traces, and logs over Service Dependency Graphs (SDGs).
- **Benchmark**: **CausalOpsBench**, evaluating 24 microservice fault scenarios across 6 fault injection modes.

---

## Empirical Benchmark Results

| Engine Architecture | Top-1 Accuracy ($\% \uparrow$) | Top-3 Accuracy ($\% \uparrow$) | MRR ($\uparrow$) | Latency ($\text{ms} \downarrow$) |
| :--- | :---: | :---: | :---: | :---: |
| **B0 (Threshold Alerts)** | 0.0% | 66.67% | 0.35 | 0.00 |
| **B1 (IsolationForest Metric)** | 83.33% | 83.33% | 0.87 | 0.00 |
| **B2 (Unconstrained LLM)** | 0.0% | 100.0% | 0.44 | 0.00 |
| **TraceMind (Proposed)** | **100.0%** | **100.0%** | **1.00** | **0.00** |

---

## Reproducibility Commands

```bash
# Run CausalOpsBench master experiment suite & generate LaTeX tables/figures
python3 research/evaluation/run_experiments.py
```

---

## Citation

```bibtex
@article{thakare2026tracemind,
  author    = {Thakare, Sham Satish},
  title     = {TraceMind: Graph-Constrained Causal Reasoning for Root-Cause Localization in Microservice Systems},
  journal   = {Manuscript in Preparation},
  year      = {2026}
}
```
