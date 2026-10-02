"""Experiment runner — generates scenarios, runs pipeline, collects metrics."""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from data_sim.simulator import ScenarioConfig, generate_scenario
from data_sim.scenarios import get_test_scenarios, get_limitation_scenarios
from pipeline.runner import run_pipeline, PipelineResult
from evaluation.metrics import (
    detection_metrics, attribution_metrics,
    random_ranking, fanout_ranking, degree_centrality_ranking,
)


def _run_single(
    cfg: ScenarioConfig,
    ablate: Optional[str] = None,
) -> Dict[str, Any]:
    """Run one scenario through the pipeline and compute all metrics."""
    df, gt = generate_scenario(cfg)
    result = run_pipeline(df, ablate=ablate)

    first_alert_t = None
    if result.n_alerts > 0:
        from detection.detector import detect_ddos
        alerts = detect_ddos(df)
        if alerts:
            first_alert_t = alerts[0].window_start

    det = detection_metrics(
        result.detected, result.suspected_bots,
        gt["bot_ips"], result.victim_ip, gt["victim_ip"],
        result.onset_times, gt["bot_onsets"],
        gt["attack_onset_global"], first_alert_t)

    # COBT attribution
    attr_cobt = attribution_metrics(
        result.ranking, gt["botmaster_ip"], gt.get("proxy_ips"))

    # Baselines (using detector's suspected bots, NOT ground truth)
    all_ips = set(df["src_ip"].unique()) | set(df["dst_ip"].unique())
    exclude = result.suspected_bots | ({result.victim_ip} if result.victim_ip else set())
    candidates = all_ips - exclude

    attr_random = attribution_metrics(
        random_ranking(candidates, cfg.seed), gt["botmaster_ip"], gt.get("proxy_ips"))
    attr_fanout = attribution_metrics(
        fanout_ranking(df, result.suspected_bots, result.onset_times,
                       result.victim_ip), gt["botmaster_ip"], gt.get("proxy_ips"))
    attr_degree = attribution_metrics(
        degree_centrality_ranking(df, result.suspected_bots, result.onset_times,
                                  result.victim_ip), gt["botmaster_ip"], gt.get("proxy_ips"))

    return {
        "scenario_id": cfg.scenario_id, "seed": cfg.seed,
        "attack_type": cfg.attack_type, "c2_style": cfg.c2_style,
        "bot_count": cfg.bot_count, "benign_hosts": cfg.benign_host_count,
        "jitter_std": cfg.jitter_std, "n_flows": len(df),
        **{f"det_{k}": v for k, v in det.items()},
        **{f"cobt_{k}": v for k, v in attr_cobt.items()},
        **{f"random_{k}": v for k, v in attr_random.items()},
        **{f"fanout_{k}": v for k, v in attr_fanout.items()},
        **{f"degree_{k}": v for k, v in attr_degree.items()},
    }


def run_all_experiments(output_dir: str = "report") -> Dict[str, pd.DataFrame]:
    """Run all experiment sets and return results DataFrames."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── Main test scenarios ─────────────────────────────────────────
    print("Running main test scenarios...")
    test_scenarios = get_test_scenarios()
    main_results = []
    for i, cfg in enumerate(test_scenarios):
        print(f"  [{i+1}/{len(test_scenarios)}] {cfg.scenario_id} "
              f"({cfg.attack_type}, {cfg.c2_style})")
        main_results.append(_run_single(cfg))
    main_df = pd.DataFrame(main_results)
    main_df.to_csv(out / "main_results.csv", index=False)

    # ── Ablation study ──────────────────────────────────────────────
    print("\nRunning ablation study...")
    # Use a representative subset (one per C2 style)
    ablation_cfgs = [s for s in test_scenarios if s.bot_count == 10
                     and s.benign_host_count == 40 and s.jitter_std == 0.5][:9]
    ablation_results = []
    for component in ["temporal", "fanout", "baseline", "graph"]:
        for cfg in ablation_cfgs:
            df_flows, gt = generate_scenario(cfg)
            result = run_pipeline(df_flows, ablate=component)
            attr = attribution_metrics(result.ranking, gt["botmaster_ip"],
                                       gt.get("proxy_ips"))
            ablation_results.append({
                "scenario_id": cfg.scenario_id, "ablated": component,
                "c2_style": cfg.c2_style, "attack_type": cfg.attack_type,
                **{f"cobt_{k}": v for k, v in attr.items()},
            })
    # Full COBT (no ablation) for comparison
    for cfg in ablation_cfgs:
        df_flows, gt = generate_scenario(cfg)
        result = run_pipeline(df_flows, ablate=None)
        attr = attribution_metrics(result.ranking, gt["botmaster_ip"],
                                   gt.get("proxy_ips"))
        ablation_results.append({
            "scenario_id": cfg.scenario_id, "ablated": "none",
            "c2_style": cfg.c2_style, "attack_type": cfg.attack_type,
            **{f"cobt_{k}": v for k, v in attr.items()},
        })
    ablation_df = pd.DataFrame(ablation_results)
    ablation_df.to_csv(out / "ablation_results.csv", index=False)

    # ── Limitation scenarios ────────────────────────────────────────
    print("\nRunning limitation scenarios...")
    limit_results = []
    for cfg in get_limitation_scenarios():
        print(f"  {cfg.scenario_id}")
        limit_results.append(_run_single(cfg))
    limit_df = pd.DataFrame(limit_results)
    limit_df.to_csv(out / "limitation_results.csv", index=False)

    print(f"\nAll results saved to {out}/")
    return {"main": main_df, "ablation": ablation_df, "limitation": limit_df}
