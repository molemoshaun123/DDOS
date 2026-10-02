"""(c) Baseline deviation scoring.

Scores how unusual a candidate's pre-attack contact pattern is compared
to its own historical behaviour (suppresses benign high-fanout servers).
"""
from __future__ import annotations
from typing import Dict, Set
import numpy as np
import pandas as pd


def score_baseline_deviation(
    candidate: str,
    suspected_bots: Set[str],
    onset_times: Dict[str, float],
    df: pd.DataFrame,
    pre_window: float = 120.0,
    baseline_bin: float = 60.0,
) -> float:
    """Baseline deviation score for a single candidate."""
    if not onset_times:
        return 0.0
    min_onset = min(onset_times.values())
    pre_start = min_onset - pre_window

    # Normal window: everything before the pre-attack window
    normal = df[(df["src_ip"] == candidate) & (df["timestamp"] < pre_start)]
    normal_duration = max(pre_start - float(df["timestamp"].min()), 1.0)
    normal_bins = max(normal_duration / baseline_bin, 1.0)
    normal_fanout = normal["dst_ip"].nunique() / normal_bins if len(normal) > 0 else 0.0

    # Pre-attack window
    pre = df[
        (df["src_ip"] == candidate) &
        (df["timestamp"] >= pre_start) & (df["timestamp"] < min_onset)
    ]
    pre_bins = max(pre_window / baseline_bin, 1.0)
    pre_fanout = pre["dst_ip"].nunique() / pre_bins if len(pre) > 0 else 0.0

    if normal_fanout > 0:
        return max(0.0, (pre_fanout - normal_fanout) / normal_fanout)
    return pre_fanout
