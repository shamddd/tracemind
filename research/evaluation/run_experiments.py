import os
import sys
import json
from datetime import datetime

# Add src to sys.path
repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src_dir = os.path.join(repo_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from icop.ml.causal_graph_engine import TraceMindEngine
from metrics import compute_causalops_metrics

def main():
    bench_path = os.path.join(repo_dir, "research", "datasets", "causalops_bench.json")
    raw_dir = os.path.join(repo_dir, "research", "results", "raw")
    processed_dir = os.path.join(repo_dir, "research", "results", "processed")
    tables_dir = os.path.join(repo_dir, "research", "tables")
    figures_dir = os.path.join(repo_dir, "research", "figures")

    for d in [raw_dir, processed_dir, tables_dir, figures_dir]:
        os.makedirs(d, exist_ok=True)

    with open(bench_path) as f:
        scenarios = json.load(f)

    modes = ["B0_ThresholdAlerts", "B1_IsolationForest", "B2_UnconstrainedLLM", "TraceMind"]
    seeds = [42, 1337, 2026]

    all_raw_results = []
    summary_by_mode = {}

    print("==================================================")
    print("Executing CausalOpsBench Experiments across RCA Engines")
    print("==================================================")

    for mode in modes:
        engine = TraceMindEngine(mode=mode)
        mode_results = []
        for seed in seeds:
            for sc in scenarios:
                res = engine.diagnose_incident(sc)
                res["seed"] = seed
                all_raw_results.append(res)
                mode_results.append(res)
                print(f"[{mode}] Seed {seed} | {sc['id']}: Top1={res['top_1']}, Top3={res['top_3']}, MRR={res['mrr']}")

        metrics = compute_causalops_metrics(mode_results)
        summary_by_mode[mode] = metrics

    # Save raw results
    raw_file = os.path.join(raw_dir, "causalops_raw_seed42.json")
    with open(raw_file, "w") as f:
        json.dump(all_raw_results, f, indent=2)

    # Save summary results
    summary_file = os.path.join(processed_dir, "causalops_summary_seed42.json")
    with open(summary_file, "w") as f:
        json.dump(summary_by_mode, f, indent=2)

    print("\nSummary Results:")
    print(json.dumps(summary_by_mode, indent=2))

    # Generate LaTeX Table
    table_path = os.path.join(tables_dir, "main_results_table.tex")
    with open(table_path, "w") as f:
        f.write("\\begin{table}[t]\n")
        f.write("\\centering\n")
        f.write("\\caption{CausalOpsBench Empirical Performance Comparison across RCA Engines.}\n")
        f.write("\\label{tab:main_results}\n")
        f.write("\\begin{tabular}{lcccc}\n")
        f.write("\\toprule\n")
        f.write("Engine Architecture & Top-1 Acc (\\% \\uparrow) & Top-3 Acc (\\% \\uparrow) & MRR (\\uparrow) & Latency (ms \\downarrow) \\\\\n")
        f.write("\\midrule\n")
        for m_name, m in summary_by_mode.items():
            clean_name = m_name.replace("_", " ")
            f.write(f"\\textbf{{{clean_name}}} & {m['top1_accuracy']}\\% & {m['top3_accuracy']}\\% & {m['mrr']} & {m['avg_latency_ms']} \\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"\nLaTeX table written to: {table_path}")

    # Generate Figure Summary Plot
    plot_path = os.path.join(figures_dir, "top1_vs_mrr.txt")
    with open(plot_path, "w") as f:
        f.write("CausalOpsBench Top-1 Accuracy vs MRR Summary\n")
        f.write("----------------------------------------------\n")
        for m_name, m in summary_by_mode.items():
            f.write(f"{m_name}: Top1={m['top1_accuracy']}% | MRR={m['mrr']} | Latency={m['avg_latency_ms']}ms\n")
    print(f"Figure plot text written to: {plot_path}")

if __name__ == "__main__":
    main()
