"""(d) Graph centrality / star-structure scoring.

Builds a directed host-interaction graph from the pre-attack window and
scores candidates by their star structure toward bots + betweenness.
"""
from __future__ import annotations
from typing import Dict, Set
import networkx as nx
import pandas as pd


def build_pre_attack_graph(
    df: pd.DataFrame,
    onset_times: Dict[str, float],
    pre_window: float = 120.0,
) -> nx.DiGraph:
    """Build a directed graph from flows in the pre-attack window."""
    if not onset_times:
        return nx.DiGraph()
    min_onset = min(onset_times.values())
    pre = df[
        (df["timestamp"] >= min_onset - pre_window) &
        (df["timestamp"] < min_onset)
    ]
    G = nx.DiGraph()
    for (src, dst), cnt in pre.groupby(["src_ip", "dst_ip"]).size().items():
        G.add_edge(src, dst, weight=int(cnt))
    return G


def score_graph_centrality(
    candidate: str,
    suspected_bots: Set[str],
    G: nx.DiGraph,
) -> float:
    """Graph score = 0.7 × star_score + 0.3 × betweenness."""
    if candidate not in G:
        return 0.0

    # Star score: fraction of out-edges going to bots
    out_edges = list(G.successors(candidate))
    if not out_edges:
        return 0.0
    bot_out = sum(1 for n in out_edges if n in suspected_bots)
    star = bot_out / len(out_edges)

    # Betweenness (normalised)
    try:
        bc = nx.betweenness_centrality(G, weight="weight", normalized=True)
        betw = bc.get(candidate, 0.0)
    except Exception:
        betw = 0.0

    return 0.7 * star + 0.3 * betw
