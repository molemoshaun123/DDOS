"""(b) Fan-out synchrony scoring.

Scores how many suspected bots a candidate contacted within a short burst.
"""
from __future__ import annotations
from typing import Dict, Set
import numpy as np
import pandas as pd


def score_fanout_synchrony(
    candidate: str,
    suspected_bots: Set[str],
    onset_times: Dict[str, float],
    df: pd.DataFrame,
    pre_window: float = 120.0,
    burst_window: float = 10.0,
) -> float:
    """Fan-out synchrony score for a single candidate."""
    if not suspected_bots or not onset_times:
        return 0.0

    min_onset = min(onset_times.values())
    contacts = df[
        (df["src_ip"] == candidate) &
        (df["dst_ip"].isin(suspected_bots)) &
        (df["timestamp"] >= min_onset - pre_window) &
        (df["timestamp"] < min_onset)
    ]
    if contacts.empty:
        return 0.0

    ts = contacts["timestamp"].sort_values().values
    dst = contacts.sort_values("timestamp")["dst_ip"].values
    max_fanout = 0

    for i in range(len(ts)):
        end = ts[i] + burst_window
        mask = (ts >= ts[i]) & (ts <= end)
        unique_bots = len(set(dst[mask]) & suspected_bots)
        max_fanout = max(max_fanout, unique_bots)

    return max_fanout / max(len(suspected_bots), 1)
