"""Adaptive weight fusion — infers C2 style and selects weight vector."""
from __future__ import annotations
from typing import Dict, List, Set, Tuple
import numpy as np
import pandas as pd


# Weight vectors: [temporal, fanout, baseline, graph]
STYLE_WEIGHTS: Dict[str, List[float]] = {
    "centralised": [0.30, 0.30, 0.15, 0.25],
    "beacon":      [0.40, 0.15, 0.25, 0.20],
    "proxied":     [0.15, 0.20, 0.25, 0.40],
}


def infer_c2_style(
    temporal_scores: Dict[str, float],
    fanout_scores: Dict[str, float],
    suspected_bots: Set[str],
    df: pd.DataFrame,
    onset_times: Dict[str, float],
    pre_window: float = 120.0,
) -> str:
    """Heuristic C2 style inference from evidence patterns."""
    # Centralised: any top candidate has high fan-out burst
    if fanout_scores and max(fanout_scores.values()) > 0.5:
        return "centralised"

    # Beacon: check top temporal candidates for periodic contact
    if temporal_scores:
        top5 = sorted(temporal_scores, key=temporal_scores.get, reverse=True)[:5]
        min_onset = min(onset_times.values()) if onset_times else 0
        for c in top5:
            contacts = df[
                (df["src_ip"] == c) & (df["dst_ip"].isin(suspected_bots)) &
                (df["timestamp"] < min_onset) &
                (df["timestamp"] >= min_onset - pre_window)
            ].sort_values("timestamp")
            if len(contacts) > 4:
                intervals = np.diff(contacts["timestamp"].values)
                if len(intervals) > 2:
                    cv = float(np.std(intervals) / (np.mean(intervals) + 1e-9))
                    if cv < 0.4:
                        return "beacon"

    # Proxied: top candidate has low direct bot coverage but high indirect
    if temporal_scores:
        top = sorted(temporal_scores, key=temporal_scores.get, reverse=True)[:3]
        min_onset = min(onset_times.values()) if onset_times else 0
        for c in top:
            direct = df[
                (df["src_ip"] == c) & (df["dst_ip"].isin(suspected_bots)) &
                (df["timestamp"] < min_onset)
            ]["dst_ip"].nunique()
            if direct < 0.3 * len(suspected_bots) and len(suspected_bots) > 3:
                return "proxied"

    return "centralised"


def get_weights(style: str) -> List[float]:
    return STYLE_WEIGHTS.get(style, STYLE_WEIGHTS["centralised"])
