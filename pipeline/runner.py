"""End-to-end pipeline: detect → attribute."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
from detection.detector import detect_ddos
from detection.onset import estimate_onsets
from attribution.ranker import rank_candidates


@dataclass
class PipelineResult:
    """Full output of one pipeline run."""
    detected: bool
    victim_ip: Optional[str]
    suspected_bots: Set[str]
    onset_times: Dict[str, float]
    ranking: List[Tuple[str, float, Dict[str, float]]]
    n_alerts: int
    inferred_style: str = ""


def run_pipeline(
    df: pd.DataFrame,
    pre_window: float = 120.0,
    ablate: Optional[str] = None,
    # Detector params
    window_width: float = 5.0,
    slide_step: float = 1.0,
    warmup: int = 10,
    z_entropy: float = 2.5,
    z_rate: float = 3.0,
    syn_threshold: float = 0.7,
) -> PipelineResult:
    """Run detection then attribution on a flow DataFrame."""
    alerts = detect_ddos(df, window_width, slide_step, warmup,
                         z_entropy, z_rate, syn_threshold)
    if not alerts:
        return PipelineResult(False, None, set(), {}, [], 0)

    bots, onsets, victim = estimate_onsets(df, alerts)
    if not bots:
        return PipelineResult(False, victim, set(), {}, [], len(alerts))

    ranking = rank_candidates(df, bots, onsets, victim, pre_window, ablate)

    return PipelineResult(
        detected=True, victim_ip=victim, suspected_bots=bots,
        onset_times=onsets, ranking=ranking, n_alerts=len(alerts))
