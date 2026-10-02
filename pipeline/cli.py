"""CLI entry-point for the COBT pipeline."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_sim.simulator import ScenarioConfig, generate_scenario, save_scenario
from pipeline.runner import run_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="COBT DDoS Detection & Attribution")
    sub = p.add_subparsers(dest="command")

    # --- generate ---
    gen = sub.add_parser("generate", help="Generate a synthetic scenario")
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--attack-type", choices=["udp_flood", "syn_flood", "http_flood"], default="syn_flood")
    gen.add_argument("--c2-style", choices=["centralised", "beacon", "proxied"], default="centralised")
    gen.add_argument("--bot-count", type=int, default=10)
    gen.add_argument("--benign-hosts", type=int, default=40)
    gen.add_argument("--output-dir", type=str, default="output")

    # --- run ---
    run = sub.add_parser("run", help="Run pipeline on a flow CSV")
    run.add_argument("flow_csv", type=str)
    run.add_argument("--pre-window", type=float, default=120.0)
    run.add_argument("--top-k", type=int, default=10)

    # --- demo ---
    sub.add_parser("demo", help="Generate + run a quick demo scenario")

    args = p.parse_args()

    if args.command == "generate":
        cfg = ScenarioConfig(
            seed=args.seed, attack_type=args.attack_type, c2_style=args.c2_style,
            bot_count=args.bot_count, benign_host_count=args.benign_hosts)
        df, gt = generate_scenario(cfg)
        fp, gp = save_scenario(df, gt, args.output_dir)
        print(f"Flows: {fp} ({len(df)} rows)")
        print(f"Ground truth: {gp}")

    elif args.command == "run":
        df = pd.read_csv(args.flow_csv)
        result = run_pipeline(df, pre_window=args.pre_window)
        print(f"Detected: {result.detected} | Alerts: {result.n_alerts}")
        print(f"Victim: {result.victim_ip} | Bots found: {len(result.suspected_bots)}")
        print(f"\nTop-{args.top_k} attribution ranking:")
        for i, (ip, score, comp) in enumerate(result.ranking[:args.top_k]):
            print(f"  {i+1}. {ip:16s}  score={score:.4f}  {comp}")

    elif args.command == "demo":
        cfg = ScenarioConfig(seed=42, bot_count=10, benign_host_count=40)
        df, gt = generate_scenario(cfg)
        result = run_pipeline(df)
        print(f"Detected: {result.detected} | Victim: {result.victim_ip}")
        print(f"Bots found: {len(result.suspected_bots)}")
        print(f"True botmaster: {gt['botmaster_ip']}")
        print(f"\nTop-5 attribution:")
        for i, (ip, score, _) in enumerate(result.ranking[:5]):
            marker = " <<<" if ip == gt["botmaster_ip"] else ""
            print(f"  {i+1}. {ip:16s}  score={score:.4f}{marker}")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
