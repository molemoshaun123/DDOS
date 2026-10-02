"""(a) Temporal precedence scoring.

Scores how consistently a candidate contacted suspected bots shortly
before each bot's estimated onset.
"""
from __future__ import annotations
from typing import Dict, Set
import numpy as np
import pandas as pd


def score_temporal_precedence(
    candidate: str,
    suspected_bots: Set[str],
    onset_times: Dict[str, float],
    df: pd.DataFrame,
    pre_window: float = 120.0,
    tau: float = 30.0,
) -> float:
    """Temporal precedence score for a single candidate."""
    lags = []
    for bot in suspected_bots:
        if bot not in onset_times:
            continue
        t0 = onset_times[bot]
        contacts = df[
            (df["src_ip"] == candidate) & (df["dst_ip"] == bot) &
            (df["timestamp"] >= t0 - pre_window) & (df["timestamp"] < t0)
        ]
        if contacts.empty:
            continue
        best_ts = float(contacts["timestamp"].max())
        lags.append(t0 - best_ts)

    if len(lags) < 2:
        return 0.0

    coverage = len(lags) / max(len(suspected_bots), 1)
    consistency = float(np.exp(-np.std(lags)))
    recency = float(np.exp(-np.mean(lags) / tau))
    return coverage * consistency * recency
