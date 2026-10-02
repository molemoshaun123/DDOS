"""Sliding-window DDoS detector using entropy + rate + SYN-ratio signals."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Dict, List
import numpy as np
import pandas as pd
from detection.features import extract_window_features


@dataclass
class Alert:
    """A single detector alert."""
    window_start: float
    window_end: float
    features: Dict[str, float]


def detect_ddos(
    df: pd.DataFrame,
    window_width: float = 5.0,
    slide_step: float = 1.0,
    warmup: int = 10,
    z_entropy: float = 2.5,
    z_rate: float = 3.0,
    syn_threshold: float = 0.7,
    min_flow_rate: float = 5.0,
) -> List[Alert]:
    """Run the sliding-window detector over flow data.

    Returns a list of Alert objects for windows that exceed thresholds.
    Uses z-scores against a running history for entropy and packet rate,
    plus an absolute SYN-ratio threshold.
    """
    timestamps = df["timestamp"].values
    if len(timestamps) == 0:
        return []

    t_min, t_max = float(timestamps[0]), float(timestamps[-1])
    alerts: List[Alert] = []

    # Running statistics
    hist_src_ent: deque = deque(maxlen=200)
    hist_pkt_rate: deque = deque(maxlen=200)

    t = t_min
    step = 0
    while t + window_width <= t_max + slide_step:
        mask = (timestamps >= t) & (timestamps < t + window_width)
        wdf = df.loc[mask]
        feats = extract_window_features(wdf, window_width)

        if step >= warmup and len(hist_src_ent) >= warmup:
            mu_ent = float(np.mean(hist_src_ent))
            sd_ent = float(np.std(hist_src_ent)) + 1e-9
            mu_pkt = float(np.mean(hist_pkt_rate))
            sd_pkt = float(np.std(hist_pkt_rate)) + 1e-9

            # Entropy DROP is suspicious (attack concentrates on one dst)
            z_e = (mu_ent - feats["src_entropy"]) / sd_ent
            z_r = (feats["packet_rate"] - mu_pkt) / sd_pkt

            triggered = (
                (z_e > z_entropy) or
                (z_r > z_rate and feats["flow_rate"] > min_flow_rate) or
                (feats["syn_ratio"] > syn_threshold and feats["flow_rate"] > min_flow_rate)
            )
            if triggered:
                alerts.append(Alert(t, t + window_width, feats))

        hist_src_ent.append(feats["src_entropy"])
        hist_pkt_rate.append(feats["packet_rate"])
        t += slide_step
        step += 1

    return alerts
