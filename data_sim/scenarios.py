"""Predefined scenario sets for tuning and testing.

Tuning seeds: 1000–1999.  Test seeds: 2000–2999.  No overlap.
"""
from __future__ import annotations
from typing import List
from data_sim.simulator import ScenarioConfig

ATTACK_TYPES = ["udp_flood", "syn_flood", "http_flood"]
C2_STYLES = ["centralised", "beacon", "proxied"]


def _make_scenarios(seed_base: int, prefix: str) -> List[ScenarioConfig]:
    scenarios: List[ScenarioConfig] = []
    idx = 0
    # 3×3 cross of attack × c2
    for at in ATTACK_TYPES:
        for c2 in C2_STYLES:
            scenarios.append(ScenarioConfig(
                seed=seed_base + idx, scenario_id=f"{prefix}_{idx:03d}",
                attack_type=at, c2_style=c2, bot_count=10, benign_host_count=40))
            idx += 1
    # Bot count sweep
    for bc in [5, 20, 50]:
        scenarios.append(ScenarioConfig(
            seed=seed_base + idx, scenario_id=f"{prefix}_{idx:03d}",
            attack_type="syn_flood", c2_style="centralised",
            bot_count=bc, benign_host_count=40))
        idx += 1
    # Jitter sweep
    for j in [0.1, 1.0, 2.0, 5.0]:
        scenarios.append(ScenarioConfig(
            seed=seed_base + idx, scenario_id=f"{prefix}_{idx:03d}",
            attack_type="syn_flood", c2_style="centralised",
            jitter_std=j, bot_count=10, benign_host_count=40))
        idx += 1
    # Noise level sweep
    for n in [80, 160]:
        scenarios.append(ScenarioConfig(
            seed=seed_base + idx, scenario_id=f"{prefix}_{idx:03d}",
            attack_type="syn_flood", c2_style="centralised",
            bot_count=10, benign_host_count=n))
        idx += 1
    return scenarios


def get_tuning_scenarios() -> List[ScenarioConfig]:
    return _make_scenarios(1000, "tune")


def get_test_scenarios() -> List[ScenarioConfig]:
    return _make_scenarios(2000, "test")


def get_limitation_scenarios() -> List[ScenarioConfig]:
    return [
        ScenarioConfig(seed=3000, scenario_id="limit_high_jitter",
                       attack_type="syn_flood", c2_style="centralised",
                       jitter_std=10.0, bot_count=10, benign_host_count=40),
        ScenarioConfig(seed=3001, scenario_id="limit_deep_proxy",
                       attack_type="syn_flood", c2_style="proxied",
                       proxy_count=3, bot_count=10, benign_host_count=40),
        ScenarioConfig(seed=3002, scenario_id="limit_idle_botmaster",
                       attack_type="syn_flood", c2_style="centralised",
                       command_lead_time=150.0, pre_attack_c2_window=60.0,
                       bot_count=10, benign_host_count=40),
        ScenarioConfig(seed=3003, scenario_id="limit_noisy_botmaster",
                       attack_type="syn_flood", c2_style="centralised",
                       bot_count=10, benign_host_count=80, benign_noise_scale=2.0),
    ]
