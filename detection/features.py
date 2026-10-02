"""Per-window feature extraction for the sliding-window detector."""
from __future__ import annotations
from typing import Dict
import numpy as np
import pandas as pd


def shannon_entropy(series: pd.Series) -> float:
    """Shannon entropy of a categorical series (bits)."""
    if len(series) == 0:
        return 0.0
    counts = series.value_counts()
    probs = counts / counts.sum()
    return float(-np.sum(probs * np.log2(probs + 1e-12)))


def extract_window_features(window_df: pd.DataFrame, width: float) -> Dict[str, float]:
    """Compute detection features for one time window.

    Returns dict with: src_entropy, dst_entropy, flow_rate, packet_rate,
    byte_rate, syn_ratio.
    """
    n = len(window_df)
    if n == 0:
        return {"src_entropy": 0.0, "dst_entropy": 0.0, "flow_rate": 0.0,
                "packet_rate": 0.0, "byte_rate": 0.0, "syn_ratio": 0.0}

    tcp = window_df[window_df["protocol"] == "TCP"]
    syn_only = tcp[tcp["flags"] == "SYN"] if len(tcp) > 0 else tcp
    syn_ratio = len(syn_only) / max(len(tcp), 1)

    return {
        "src_entropy": shannon_entropy(window_df["src_ip"]),
        "dst_entropy": shannon_entropy(window_df["dst_ip"]),
        "flow_rate": n / max(width, 1e-6),
        "packet_rate": float(window_df["packets"].sum()) / max(width, 1e-6),
        "byte_rate": float(window_df["bytes"].sum()) / max(width, 1e-6),
        "syn_ratio": syn_ratio,
    }
