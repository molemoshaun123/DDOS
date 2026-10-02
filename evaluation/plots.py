"""Plot generators for the report."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


def set_style():
    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["savefig.bbox"] = "tight"


def plot_detection_by_attack_type(df: pd.DataFrame, out: Path):
    """Bar chart of detection P/R/F1 grouped by attack type."""
    set_style()
    metrics = ["det_precision", "det_recall", "det_f1"]
    labels = ["Precision", "Recall", "F1"]
    grouped = df.groupby("attack_type")[metrics].mean()

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(grouped))
    w = 0.25
    for i, (col, label) in enumerate(zip(metrics, labels)):
        ax.bar(x + i * w, grouped[col], w, label=label)
    ax.set_xticks(x + w)
    ax.set_xticklabels(grouped.index, rotation=0)
    ax.set_ylabel("Score")
    ax.set_title("Detection Performance by Attack Type")
    ax.legend()
    ax.set_ylim(0, 1.1)
    fig.savefig(out / "detection_by_attack_type.png")
    plt.close(fig)


def plot_attribution_comparison(df: pd.DataFrame, out: Path):
    """Grouped bar chart comparing COBT vs baselines on Top-1/3/5 and MRR."""
    set_style()
    methods = {"COBT": "cobt", "Random": "random", "Fan-out": "fanout",
               "Degree Cent.": "degree"}
    metrics_keys = ["top1", "top3", "top5", "mrr"]
    metric_labels = ["Top-1", "Top-3", "Top-5", "MRR"]

    data = []
    for label, prefix in methods.items():
        for mk, ml in zip(metrics_keys, metric_labels):
            col = f"{prefix}_{mk}"
            if col in df.columns:
                data.append({"Method": label, "Metric": ml,
                             "Value": df[col].mean()})
    plot_df = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=plot_df, x="Metric", y="Value", hue="Method", ax=ax)
    ax.set_title("Attribution: COBT vs Baselines")
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Score")
    fig.savefig(out / "attribution_comparison.png")
    plt.close(fig)


def plot_attribution_by_c2_style(df: pd.DataFrame, out: Path):
    """COBT Top-1/MRR by C2 style."""
    set_style()
    grouped = df.groupby("c2_style")[["cobt_top1", "cobt_top3", "cobt_top5", "cobt_mrr"]].mean()

    fig, ax = plt.subplots(figsize=(8, 5))
    grouped.plot(kind="bar", ax=ax)
    ax.set_title("COBT Attribution by C2 Style")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.1)
    ax.set_xticklabels(grouped.index, rotation=0)
    ax.legend(["Top-1", "Top-3", "Top-5", "MRR"])
    fig.savefig(out / "attribution_by_c2_style.png")
    plt.close(fig)


def plot_ablation(df: pd.DataFrame, out: Path):
    """Ablation study: effect of removing each component."""
    set_style()
    grouped = df.groupby("ablated")[["cobt_top1", "cobt_mrr"]].mean()
    # Reorder
    order = ["none", "temporal", "fanout", "baseline", "graph"]
    grouped = grouped.reindex([o for o in order if o in grouped.index])
    labels = {"none": "Full COBT", "temporal": "−Temporal", "fanout": "−Fan-out",
              "baseline": "−Baseline", "graph": "−Graph"}
    grouped.index = [labels.get(i, i) for i in grouped.index]

    fig, ax = plt.subplots(figsize=(8, 5))
    grouped.plot(kind="bar", ax=ax)
    ax.set_title("Ablation Study")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.1)
    ax.set_xticklabels(grouped.index, rotation=15)
    ax.legend(["Top-1 Accuracy", "MRR"])
    fig.savefig(out / "ablation_study.png")
    plt.close(fig)


def plot_limitation_scenarios(df: pd.DataFrame, out: Path):
    """Limitation scenarios: COBT performance under stress."""
    set_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(df))
    w = 0.2
    ax.bar(x - w, df["cobt_top1"], w, label="Top-1")
    ax.bar(x, df["cobt_top3"], w, label="Top-3")
    ax.bar(x + w, df["cobt_top5"], w, label="Top-5")
    ax.set_xticks(x)
    labels = df["scenario_id"].str.replace("limit_", "").str.replace("_", " ").str.title()
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylabel("Accuracy")
    ax.set_title("Limitation Scenarios — Where COBT Struggles")
    ax.legend()
    ax.set_ylim(0, 1.1)
    fig.savefig(out / "limitation_scenarios.png")
    plt.close(fig)


def plot_detection_delay(df: pd.DataFrame, out: Path):
    """Detection delay by attack type."""
    set_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df, x="attack_type", y="det_detection_delay", ax=ax)
    ax.set_title("Detection Delay by Attack Type")
    ax.set_ylabel("Delay (seconds)")
    ax.set_xlabel("Attack Type")
    fig.savefig(out / "detection_delay.png")
    plt.close(fig)


def plot_jitter_sensitivity(df: pd.DataFrame, out: Path):
    """Attribution performance vs jitter."""
    set_style()
    jitter_df = df[df["c2_style"] == "centralised"].sort_values("jitter_std")
    if len(jitter_df) < 2:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(jitter_df["jitter_std"], jitter_df["cobt_top1"], "o-", label="Top-1")
    ax.plot(jitter_df["jitter_std"], jitter_df["cobt_mrr"], "s-", label="MRR")
    ax.set_xlabel("Jitter Std Dev (seconds)")
    ax.set_ylabel("Score")
    ax.set_title("Attribution Sensitivity to C2 Jitter")
    ax.legend()
    ax.set_ylim(0, 1.1)
    fig.savefig(out / "jitter_sensitivity.png")
    plt.close(fig)


def plot_bot_count_sensitivity(df: pd.DataFrame, out: Path):
    """Attribution performance vs bot count."""
    set_style()
    bc_df = df[(df["c2_style"] == "centralised") &
               (df["attack_type"] == "syn_flood")].sort_values("bot_count")
    if len(bc_df) < 2:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(bc_df["bot_count"], bc_df["cobt_top1"], "o-", label="Top-1")
    ax.plot(bc_df["bot_count"], bc_df["cobt_mrr"], "s-", label="MRR")
    ax.set_xlabel("Bot Count")
    ax.set_ylabel("Score")
    ax.set_title("Attribution Sensitivity to Bot Count")
    ax.legend()
    ax.set_ylim(0, 1.1)
    fig.savefig(out / "bot_count_sensitivity.png")
    plt.close(fig)


def generate_all_plots(results: dict, output_dir: str = "report"):
    """Generate all report plots from experiment results."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    main_df = results["main"]
    ablation_df = results["ablation"]
    limit_df = results["limitation"]

    plot_detection_by_attack_type(main_df, out)
    plot_attribution_comparison(main_df, out)
    plot_attribution_by_c2_style(main_df, out)
    plot_ablation(ablation_df, out)
    plot_limitation_scenarios(limit_df, out)
    plot_detection_delay(main_df, out)
    plot_jitter_sensitivity(main_df, out)
    plot_bot_count_sensitivity(main_df, out)

    print(f"All plots saved to {out}/")
