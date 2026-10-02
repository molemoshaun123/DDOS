"""Main simulator: orchestrates benign, C2, and attack traffic into scenarios.

SAFETY: generates data files only — no sockets, no packets, no real network activity.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from data_sim.profiles import (
    generate_web_browsing, generate_dns_queries, generate_ntp_sync,
    generate_p2p_chatter, generate_admin_workstation,
    generate_monitoring_server, generate_update_pusher, generate_load_balancer,
)
from data_sim.attacks import generate_udp_flood, generate_syn_flood, generate_http_flood
from data_sim.c2 import generate_centralised_c2, generate_beacon_c2, generate_proxied_c2

FLOW_COLUMNS = [
    "timestamp", "src_ip", "dst_ip", "src_port", "dst_port",
    "protocol", "packets", "bytes", "flags", "duration",
]


@dataclass
class ScenarioConfig:
    """All parameters for one synthetic scenario."""
    seed: int = 42
    scenario_id: str = "scenario_001"
    duration_seconds: float = 300.0
    attack_onset: float = 200.0
    attack_duration: float = 80.0
    pre_attack_c2_window: float = 60.0
    benign_host_count: int = 40
    bot_count: int = 10
    proxy_count: int = 2
    attack_type: str = "syn_flood"       # udp_flood | syn_flood | http_flood
    c2_style: str = "centralised"        # centralised | beacon | proxied
    jitter_std: float = 0.5
    command_lead_time: float = 5.0
    beacon_period: float = 10.0
    multi_flow_commands: bool = True
    late_bot_fraction: float = 0.1
    late_bot_delay_mean: float = 10.0
    unresponsive_bot_fraction: float = 0.1
    benign_noise_scale: float = 1.0
    attack_flows_per_second: float = 10.0

    def validate(self) -> None:
        assert self.duration_seconds > 0
        assert 0 < self.attack_onset < self.duration_seconds
        assert self.bot_count >= 1
        assert self.attack_type in ("udp_flood", "syn_flood", "http_flood")
        assert self.c2_style in ("centralised", "beacon", "proxied")
        assert 0 <= self.late_bot_fraction < 1
        assert 0 <= self.unresponsive_bot_fraction < 1
        assert (self.late_bot_fraction + self.unresponsive_bot_fraction) < 1


@dataclass
class NetworkTopology:
    victim_ip: str
    botmaster_ip: str
    proxy_ips: List[str]
    bot_ips: List[str]
    benign_ips: List[str]
    web_server_ips: List[str]
    dns_server_ips: List[str]
    ntp_server_ip: str
    monitoring_server_ip: str
    admin_workstation_ip: str
    update_server_ip: str
    load_balancer_ip: str


def _assign_ips(cfg: ScenarioConfig) -> NetworkTopology:
    return NetworkTopology(
        victim_ip="10.99.0.1",
        botmaster_ip="10.0.0.1",
        proxy_ips=[f"10.0.1.{i+1}" for i in range(cfg.proxy_count)],
        bot_ips=[f"10.1.0.{i+1}" for i in range(cfg.bot_count)],
        benign_ips=[f"10.2.{i // 254}.{i % 254 + 1}" for i in range(cfg.benign_host_count)],
        web_server_ips=[f"10.100.0.{i+1}" for i in range(5)],
        dns_server_ips=["10.200.0.1", "10.200.0.2"],
        ntp_server_ip="10.200.1.1",
        monitoring_server_ip="10.200.5.1",
        admin_workstation_ip="10.200.4.1",
        update_server_ip="10.200.2.1",
        load_balancer_ip="10.200.3.1",
    )


def generate_scenario(cfg: ScenarioConfig) -> Tuple[pd.DataFrame, dict]:
    """Generate a full synthetic scenario. Returns (flows_df, ground_truth)."""
    cfg.validate()
    rng = np.random.default_rng(cfg.seed)
    topo = _assign_ips(cfg)
    all_flows: List[dict] = []
    t0, t1 = 0.0, cfg.duration_seconds

    # Hosts managed by decoys (includes bots — makes decoys realistic)
    managed = topo.benign_ips + topo.bot_ips

    # --- Benign traffic from regular hosts ---
    for hip in topo.benign_ips:
        all_flows.extend(generate_web_browsing(
            rng, hip, topo.web_server_ips, t0, t1,
            mean_session_gap=30.0 / cfg.benign_noise_scale))
        all_flows.extend(generate_dns_queries(
            rng, hip, topo.dns_server_ips, t0, t1,
            mean_interval=5.0 / cfg.benign_noise_scale))
        if rng.random() < 0.3:
            all_flows.extend(generate_ntp_sync(rng, hip, topo.ntp_server_ip, t0, t1))
        if rng.random() < 0.2:
            peers = list(rng.choice(topo.benign_ips, size=min(3, len(topo.benign_ips)), replace=False))
            all_flows.extend(generate_p2p_chatter(rng, hip, peers, t0, t1))

    # Bots also have benign background
    for bip in topo.bot_ips:
        all_flows.extend(generate_web_browsing(
            rng, bip, topo.web_server_ips, t0, t1, mean_session_gap=40.0))
        all_flows.extend(generate_dns_queries(
            rng, bip, topo.dns_server_ips, t0, t1, mean_interval=8.0))

    # Botmaster benign background (it's a real machine)
    all_flows.extend(generate_web_browsing(
        rng, topo.botmaster_ip, topo.web_server_ips, t0, t1, mean_session_gap=60.0))
    all_flows.extend(generate_dns_queries(
        rng, topo.botmaster_ip, topo.dns_server_ips, t0, t1, mean_interval=10.0))

    # Proxies benign background
    if cfg.c2_style == "proxied":
        for pip in topo.proxy_ips:
            all_flows.extend(generate_web_browsing(
                rng, pip, topo.web_server_ips, t0, t1, mean_session_gap=50.0))

    # --- Decoy / infrastructure traffic ---
    all_flows.extend(generate_admin_workstation(
        rng, topo.admin_workstation_ip, managed, t0, t1, mean_interval=15.0))
    all_flows.extend(generate_monitoring_server(
        rng, topo.monitoring_server_ip, managed, t0, t1, check_period=30.0))
    all_flows.extend(generate_update_pusher(
        rng, topo.update_server_ip, managed, t0, t1, push_interval=120.0))
    all_flows.extend(generate_load_balancer(
        rng, topo.load_balancer_ip, managed, t0, t1, mean_interval=2.0))

    # --- Per-bot onset times ---
    n_unresp = int(cfg.bot_count * cfg.unresponsive_bot_fraction)
    n_late = int(cfg.bot_count * cfg.late_bot_fraction)
    shuffled = list(topo.bot_ips)
    rng.shuffle(shuffled)
    normal_bots = shuffled[:cfg.bot_count - n_unresp - n_late]
    late_bots = shuffled[cfg.bot_count - n_unresp - n_late:cfg.bot_count - n_unresp]
    unresp_bots = shuffled[cfg.bot_count - n_unresp:]

    bot_onsets: Dict[str, float] = {}
    for b in normal_bots:
        bot_onsets[b] = cfg.attack_onset + abs(rng.normal(0, 0.5))
    for b in late_bots:
        bot_onsets[b] = cfg.attack_onset + abs(rng.normal(cfg.late_bot_delay_mean, 3.0))

    # --- C2 traffic ---
    if cfg.c2_style == "centralised":
        c2f, c2t = generate_centralised_c2(
            rng, topo.botmaster_ip, topo.bot_ips, bot_onsets,
            jitter_std=cfg.jitter_std, command_lead_time=cfg.command_lead_time,
            multi_flow=cfg.multi_flow_commands)
    elif cfg.c2_style == "beacon":
        c2f, c2t = generate_beacon_c2(
            rng, topo.botmaster_ip, topo.bot_ips, bot_onsets,
            beacon_period=cfg.beacon_period, jitter_std=cfg.jitter_std,
            pre_window=cfg.pre_attack_c2_window, multi_flow=cfg.multi_flow_commands)
    else:
        c2f, c2t = generate_proxied_c2(
            rng, topo.botmaster_ip, topo.proxy_ips, topo.bot_ips, bot_onsets,
            jitter_std=cfg.jitter_std, multi_flow=cfg.multi_flow_commands)
    all_flows.extend(c2f)

    # --- Attack traffic ---
    atk_gen = {"udp_flood": generate_udp_flood, "syn_flood": generate_syn_flood,
               "http_flood": generate_http_flood}[cfg.attack_type]
    for bip, onset in bot_onsets.items():
        dur = min(cfg.attack_duration, cfg.duration_seconds - onset)
        if dur > 0:
            all_flows.extend(atk_gen(rng, bip, topo.victim_ip, onset,
                                     duration=dur, flows_per_second=cfg.attack_flows_per_second))

    # --- Build DataFrame (NO labels) ---
    df = pd.DataFrame(all_flows, columns=FLOW_COLUMNS)
    df = df.sort_values("timestamp").reset_index(drop=True)

    ground_truth = {
        "seed": cfg.seed, "scenario_id": cfg.scenario_id,
        "botmaster_ip": topo.botmaster_ip,
        "proxy_ips": topo.proxy_ips if cfg.c2_style == "proxied" else [],
        "bot_ips": topo.bot_ips, "victim_ip": topo.victim_ip,
        "attack_type": cfg.attack_type, "c2_style": cfg.c2_style,
        "attack_onset_global": cfg.attack_onset,
        "bot_onsets": bot_onsets, "unresponsive_bots": unresp_bots,
        "late_bots": late_bots, "c2_contact_times": c2t,
        "decoy_ips": [topo.monitoring_server_ip, topo.admin_workstation_ip,
                      topo.update_server_ip, topo.load_balancer_ip],
        "infrastructure_ips": (topo.web_server_ips + topo.dns_server_ips +
            [topo.ntp_server_ip, topo.monitoring_server_ip,
             topo.admin_workstation_ip, topo.update_server_ip, topo.load_balancer_ip]),
        "config": asdict(cfg),
    }
    return df, ground_truth


def save_scenario(df: pd.DataFrame, ground_truth: dict,
                  output_dir: str | Path, scenario_id: str | None = None
                  ) -> Tuple[Path, Path]:
    """Save flows CSV and ground-truth JSON to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    sid = scenario_id or ground_truth.get("scenario_id", "scenario")
    fp = out / f"{sid}_flows.csv"
    gp = out / f"{sid}_ground_truth.json"
    df.to_csv(fp, index=False)
    with open(gp, "w") as f:
        json.dump(ground_truth, f, indent=2, default=str)
    return fp, gp
