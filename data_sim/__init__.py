"""
data_sim — Synthetic flow-level traffic simulator for DDoS research.

SAFETY: All functions generate data rows only. No sockets, no packet
crafting, no real network activity is performed.
"""

from data_sim.simulator import ScenarioConfig, generate_scenario, save_scenario
from data_sim.scenarios import (
    get_tuning_scenarios,
    get_test_scenarios,
    get_limitation_scenarios,
)

__all__ = [
    "ScenarioConfig",
    "generate_scenario",
    "save_scenario",
    "get_tuning_scenarios",
    "get_test_scenarios",
    "get_limitation_scenarios",
]
