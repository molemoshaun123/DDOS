"""Tests for simulator, detector, attribution, pipeline, and ground-truth leakage."""
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent

from data_sim.simulator import ScenarioConfig, generate_scenario, save_scenario, FLOW_COLUMNS
from data_sim.scenarios import get_tuning_scenarios, get_test_scenarios, get_limitation_scenarios
from detection.detector import detect_ddos
from detection.onset import estimate_onsets
from attribution.ranker import rank_candidates
from pipeline.runner import run_pipeline


# ── Simulator tests ──────────────────────────────────────────────────

class TestSimulator:
    CFG = ScenarioConfig(seed=42, bot_count=5, benign_host_count=10, duration_seconds=100, attack_onset=50)

    def test_generates_dataframe(self):
        df, gt = generate_scenario(self.CFG)
        assert isinstance(df, pd.DataFrame) and len(df) > 0

    def test_columns(self):
        df, _ = generate_scenario(self.CFG)
        assert list(df.columns) == FLOW_COLUMNS

    def test_no_labels_in_flows(self):
        df, _ = generate_scenario(self.CFG)
        bad = {"label", "actor", "is_attack", "is_bot", "is_c2"}
        assert bad.isdisjoint(set(df.columns))

    def test_ground_truth_fields(self):
        _, gt = generate_scenario(self.CFG)
        for k in ["botmaster_ip", "bot_ips", "victim_ip", "attack_type", "c2_style", "bot_onsets"]:
            assert k in gt

    def test_deterministic(self):
        df1, gt1 = generate_scenario(self.CFG)
        df2, gt2 = generate_scenario(self.CFG)
        pd.testing.assert_frame_equal(df1, df2)

    def test_sorted(self):
        df, _ = generate_scenario(self.CFG)
        assert df["timestamp"].is_monotonic_increasing

    def test_all_attack_types(self):
        for at in ["udp_flood", "syn_flood", "http_flood"]:
            df, gt = generate_scenario(ScenarioConfig(seed=1, attack_type=at, bot_count=3, benign_host_count=5, duration_seconds=60, attack_onset=30))
            assert len(df) > 0 and gt["attack_type"] == at

    def test_all_c2_styles(self):
        for c2 in ["centralised", "beacon", "proxied"]:
            df, gt = generate_scenario(ScenarioConfig(seed=1, c2_style=c2, bot_count=3, benign_host_count=5, duration_seconds=60, attack_onset=30))
            assert len(df) > 0 and gt["c2_style"] == c2

    def test_unresponsive_bots(self):
        cfg = ScenarioConfig(seed=42, bot_count=10, benign_host_count=5, duration_seconds=100, attack_onset=50, unresponsive_bot_fraction=0.3)
        _, gt = generate_scenario(cfg)
        for b in gt["unresponsive_bots"]:
            assert b not in gt["bot_onsets"]

    def test_save_load(self, tmp_path):
        df, gt = generate_scenario(self.CFG)
        fp, gp = save_scenario(df, gt, tmp_path)
        loaded = pd.read_csv(fp)
        assert len(loaded) == len(df)
        with open(gp) as f:
            jgt = json.load(f)
        assert jgt["botmaster_ip"] == gt["botmaster_ip"]

    def test_seeds_disjoint(self):
        t_seeds = {s.seed for s in get_tuning_scenarios()}
        e_seeds = {s.seed for s in get_test_scenarios()}
        assert t_seeds.isdisjoint(e_seeds)


# ── Detector tests ───────────────────────────────────────────────────

class TestDetector:
    def test_detects_attack(self):
        cfg = ScenarioConfig(seed=42, bot_count=10, benign_host_count=20, duration_seconds=300)
        df, gt = generate_scenario(cfg)
        alerts = detect_ddos(df)
        assert len(alerts) > 0

    def test_onset_estimation(self):
        cfg = ScenarioConfig(seed=42, bot_count=10, benign_host_count=20, duration_seconds=300)
        df, gt = generate_scenario(cfg)
        alerts = detect_ddos(df)
        bots, onsets, victim = estimate_onsets(df, alerts)
        assert len(bots) > 0
        assert victim is not None


# ── Attribution tests ────────────────────────────────────────────────

class TestAttribution:
    def test_ranks_candidates(self):
        cfg = ScenarioConfig(seed=42, bot_count=10, benign_host_count=20, duration_seconds=300)
        df, gt = generate_scenario(cfg)
        alerts = detect_ddos(df)
        bots, onsets, victim = estimate_onsets(df, alerts)
        ranking = rank_candidates(df, bots, onsets, victim)
        assert len(ranking) > 0
        # Botmaster should be in candidate list
        ranked_ips = [ip for ip, _, _ in ranking]
        assert gt["botmaster_ip"] in ranked_ips


# ── Pipeline tests ───────────────────────────────────────────────────

class TestPipeline:
    def test_end_to_end(self):
        cfg = ScenarioConfig(seed=42, bot_count=10, benign_host_count=20, duration_seconds=300)
        df, gt = generate_scenario(cfg)
        result = run_pipeline(df)
        assert result.detected
        assert len(result.ranking) > 0

    def test_ablation_runs(self):
        cfg = ScenarioConfig(seed=42, bot_count=10, benign_host_count=20, duration_seconds=300)
        df, _ = generate_scenario(cfg)
        for comp in ["temporal", "fanout", "baseline", "graph"]:
            result = run_pipeline(df, ablate=comp)
            assert result.detected


# ── Ground-truth leakage test ────────────────────────────────────────

class TestNoLeakage:
    FORBIDDEN = ["ground_truth", "botmaster_ip", "bot_ips", "true_label",
                 "true_onset", "unresponsive_bots", "c2_contact_times",
                 "from evaluation", "import evaluation"]

    def _check(self, module: str):
        d = ROOT / module
        if not d.is_dir():
            pytest.skip(f"{module}/ not yet created")
        for f in d.glob("*.py"):
            src = f.read_text(encoding="utf-8").lower()
            for pat in self.FORBIDDEN:
                assert pat not in src, f"LEAKAGE: '{pat}' in {f.name}"

    def test_detection_no_leakage(self):
        self._check("detection")

    def test_attribution_no_leakage(self):
        self._check("attribution")


# ── Safety test ──────────────────────────────────────────────────────

class TestSafety:
    def test_no_socket_imports(self):
        forbidden = {"socket", "scapy", "dpkt", "pcapy", "rawsocket"}
        for f in (ROOT / "data_sim").glob("*.py"):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        assert a.name not in forbidden
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert node.module.split(".")[0] not in forbidden
