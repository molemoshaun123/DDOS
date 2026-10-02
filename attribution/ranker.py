"""Top-level COBT ranker — orchestrates all four scorers + fusion."""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from attribution.temporal import score_temporal_precedence
from attribution.fanout import score_fanout_synchrony
from attribution.baseline import score_baseline_deviation
from attribution.graph import build_pre_attack_graph, score_graph_centrality
from attribution.fusion import infer_c2_style, get_weights


def _minmax(scores: Dict[str, float]) -> Dict[str, float]:
    """Min-max normalise scores to [0, 1]."""
    if not scores:
        return scores
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    rng = hi - lo if hi - lo > 1e-12 else 1.0
    return {k: (v - lo) / rng for k, v in scores.items()}


def rank_candidates(
    df: pd.DataFrame,
    suspected_bots: Set[str],
    onset_times: Dict[str, float],
    victim_ip: Optional[str],
    pre_window: float = 120.0,
    ablate: Optional[str] = None,
) -> List[Tuple[str, float, Dict[str, float]]]:
    """Run full COBT attribution and return ranked candidate list.

    Args:
        ablate: if set, skip this component ('temporal','fanout','baseline','graph').

    Returns list of (candidate_ip, final_score, component_scores), descending.
    """
    if not suspected_bots or not onset_times:
        return []

    # Candidates = all observed IPs minus suspected bots and victim
    all_ips = set(df["src_ip"].unique()) | set(df["dst_ip"].unique())
    exclude = suspected_bots | ({victim_ip} if victim_ip else set())
    candidates = all_ips - exclude

    # Build pre-attack graph once
    G = build_pre_attack_graph(df, onset_times, pre_window)

    # Score each candidate on all four components
    t_scores: Dict[str, float] = {}
    f_scores: Dict[str, float] = {}
    b_scores: Dict[str, float] = {}
    g_scores: Dict[str, float] = {}

    for c in candidates:
        t_scores[c] = 0.0 if ablate == "temporal" else score_temporal_precedence(
            c, suspected_bots, onset_times, df, pre_window)
        f_scores[c] = 0.0 if ablate == "fanout" else score_fanout_synchrony(
            c, suspected_bots, onset_times, df, pre_window)
        b_scores[c] = 0.0 if ablate == "baseline" else score_baseline_deviation(
            c, suspected_bots, onset_times, df, pre_window)
        g_scores[c] = 0.0 if ablate == "graph" else score_graph_centrality(
            c, suspected_bots, G)

    # Normalise
    t_norm = _minmax(t_scores)
    f_norm = _minmax(f_scores)
    b_norm = _minmax(b_scores)
    g_norm = _minmax(g_scores)

    # Infer C2 style and get weights
    style = infer_c2_style(t_scores, f_scores, suspected_bots, df, onset_times, pre_window)
    w = get_weights(style)

    # Fuse
    results = []
    for c in candidates:
        components = {
            "temporal": t_norm.get(c, 0), "fanout": f_norm.get(c, 0),
            "baseline": b_norm.get(c, 0), "graph": g_norm.get(c, 0),
        }
        final = (w[0] * components["temporal"] + w[1] * components["fanout"] +
                 w[2] * components["baseline"] + w[3] * components["graph"])
        results.append((c, final, components))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
