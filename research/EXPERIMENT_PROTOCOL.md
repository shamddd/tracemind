# Frozen Experimental Protocol — TraceMind Benchmarking

**Author**: Sham Satish Thakare (`151498087+shamddd@users.noreply.github.com`)  
**Repository**: `intelligent-cloud-observability-platform` (`tracemind`)

---

## 1. Experimental Environment & Seed Control

- **Execution Engine**: Python 3.12, scikit-learn, OpenTelemetry Collector, NetworkX graph engine.
- **Random Seeds**: `{42, 1337, 2026}` (3 random seeds per scenario for statistical error bars).
- **Microservice Architecture**: 4 interconnected services (Gateway $\to$ Auth $\to$ Payment $\to$ Inventory/Database).

---

## 2. Benchmark Scenarios (`CausalOpsBench`)

| Scenario ID | Name | Injected Fault Target | Microservice Outage Dynamics | Expected Root Cause |
| :-: | :--- | :--- | :--- | :--- |
| **S01** | CPU Saturation | Payment Service | 100% CPU thread lock; downstream Gateway timeouts. | `Payment` |
| **S02** | Memory Leak | Auth Service | RAM exhaustion -> OOM container crash. | `Auth` |
| **S03** | DB Connection Exhaustion | Inventory Service | Connection pool starvation; API 500 errors. | `Inventory` |
| **S04** | Network Packet Latency | Auth -> DB Link | 250ms synthetic delay added across RPC link. | `Auth` |
| **S05** | Cascading Retry Storm | Payment Service | Transient DB timeout causing 10x RPC retries. | `Payment` |
| **S06** | Dependency Crash | Database Container | Unexpected process SIGKILL. | `Database` |

---

## 3. Evaluation Metrics

1. **Top-1 RCA Accuracy ($\% \uparrow$)**: Percentage of incidents where the true root-cause service is ranked #1.
2. **Top-3 RCA Accuracy ($\% \uparrow$)**: Percentage of incidents where the true root-cause service is within top 3.
3. **Mean Reciprocal Rank ($MRR \uparrow$)**: Reciprocal rank of the true root cause in candidate diagnosis list.
4. **Mean Time to Diagnosis ($MTTD \text{ ms} \downarrow$)**: Execution duration for candidate diagnosis generation.
