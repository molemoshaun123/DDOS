"""Run full evaluation: experiments + plots + print tables."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluation.experiments import run_all_experiments
from evaluation.plots import generate_all_plots
import pandas as pd


def print_table(title: str, df: pd.DataFrame, cols: list):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(df[cols].to_string(index=False, float_format="%.3f"))


def main():
    results = run_all_experiments("report")
    generate_all_plots(results, "report")

    main_df = results["main"]
    abl_df = results["ablation"]
    lim_df = results["limitation"]

    # Detection table
    det_cols = ["attack_type", "det_precision", "det_recall", "det_f1",
                "det_fpr", "det_detection_delay"]
    det_summary = main_df.groupby("attack_type")[
        ["det_precision", "det_recall", "det_f1", "det_fpr", "det_detection_delay"]
    ].mean().reset_index()
    print_table("DETECTION METRICS (by attack type)", det_summary, det_summary.columns.tolist())

    # Attribution comparison table
    print(f"\n{'='*60}")
    print(f"  ATTRIBUTION: COBT vs BASELINES (averaged)")
    print(f"{'='*60}")
    for method, prefix in [("COBT", "cobt"), ("Random", "random"),
                            ("Fan-out", "fanout"), ("Degree Cent.", "degree")]:
        t1 = main_df[f"{prefix}_top1"].mean()
        t3 = main_df[f"{prefix}_top3"].mean()
        t5 = main_df[f"{prefix}_top5"].mean()
        mrr = main_df[f"{prefix}_mrr"].mean()
        print(f"  {method:15s}  Top-1={t1:.3f}  Top-3={t3:.3f}  Top-5={t5:.3f}  MRR={mrr:.3f}")

    # Attribution by C2 style
    c2_summary = main_df.groupby("c2_style")[
        ["cobt_top1", "cobt_top3", "cobt_top5", "cobt_mrr"]
    ].mean().reset_index()
    print_table("COBT ATTRIBUTION BY C2 STYLE", c2_summary, c2_summary.columns.tolist())

    # Ablation table
    abl_summary = abl_df.groupby("ablated")[
        ["cobt_top1", "cobt_top3", "cobt_top5", "cobt_mrr"]
    ].mean().reset_index()
    print_table("ABLATION STUDY", abl_summary, abl_summary.columns.tolist())

    # Limitation table
    lim_cols = ["scenario_id", "cobt_top1", "cobt_top3", "cobt_top5", "cobt_mrr"]
    print_table("LIMITATION SCENARIOS", lim_df, lim_cols)

    print(f"\nPlots saved in report/")


if __name__ == "__main__":
    main()
