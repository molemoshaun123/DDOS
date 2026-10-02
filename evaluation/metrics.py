"""Detection and attribution metrics."""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
import numpy as np


# ── Detection metrics ────────────────────────────────────────────────

def detection_metrics(
    detected: bool,
    suspected_bots: Set[str],
    true_bots: List[str],
    victim_found: Optional[str],
    true_victim: str,
    onset_times: Dict[str, float],
    true_onsets: Dict[str, float],
    attack_onset_global: float,
    first_alert_time: Optional[float] = None,
) -> Dict[str, float]:
    """Compute detection precision, recall, F1, FPR, and delay."""
    true_set = set(true_bots)
    # Only bots that actually attack (have onsets)
    attacking_bots = set(true_onsets.keys())

    tp = len(suspected_bots & attacking_bots)
    fp = len(suspected_bots - attacking_bots)
    fn = len(attacking_bots - suspected_bots)
    # True negatives: everything that isn't an attacking bot and wasn't suspected
    # We approximate with attacking_bots count
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    fpr = fp / max(fp + 1, 1)  # simplified

    delay = 0.0
    if first_alert_time is not None:
        delay = max(0, first_alert_time - attack_onset_global)

    victim_correct = 1.0 if victim_found == true_victim else 0.0

    # Mean onset error
    onset_errors = []
    for bot, est_t in onset_times.items():
        if bot in true_onsets:
            onset_errors.append(abs(est_t - true_onsets[bot]))
    mean_onset_error = float(np.mean(onset_errors)) if onset_errors else float("inf")

    return {
        "precision": precision, "recall": recall, "f1": f1, "fpr": fpr,
        "detection_delay": delay, "victim_correct": victim_correct,
        "mean_onset_error": mean_onset_error,
    }


# ── Attribution metrics ──────────────────────────────────────────────

def attribution_metrics(
    ranking: List[Tuple[str, float, dict]],
    true_controller: str,
    proxy_ips: Optional[List[str]] = None,
) -> Dict[str, float]:
    """Compute Top-K accuracy and MRR for attribution.

    For proxied C2, also checks if a proxy is ranked highly.
    """
    ranked_ips = [ip for ip, _, _ in ranking]
    proxies = set(proxy_ips or [])
    targets = {true_controller} | proxies  # any of these counts as partial success

    def _rank_of(target_set: set) -> Optional[int]:
        for i, ip in enumerate(ranked_ips):
            if ip in target_set:
                return i + 1
        return None

    # Strict: only true botmaster
    rank_strict = _rank_of({true_controller})
    # Lenient: botmaster or any proxy
    rank_lenient = _rank_of(targets)

    def _topk(rank: Optional[int], k: int) -> float:
        return 1.0 if rank is not None and rank <= k else 0.0

    def _mrr(rank: Optional[int]) -> float:
        return 1.0 / rank if rank is not None else 0.0

    return {
        "top1": _topk(rank_strict, 1),
        "top3": _topk(rank_strict, 3),
        "top5": _topk(rank_strict, 5),
        "mrr": _mrr(rank_strict),
        "top1_lenient": _topk(rank_lenient, 1),
        "top3_lenient": _topk(rank_lenient, 3),
        "top5_lenient": _topk(rank_lenient, 5),
        "mrr_lenient": _mrr(rank_lenient),
        "rank": rank_strict if rank_strict else len(ranked_ips) + 1,
    }


# ── Baseline rankers ─────────────────────────────────────────────────

def random_ranking(
    candidates: Set[str], seed: int = 0,
) -> List[Tuple[str, float, dict]]:
    """Random baseline ranking."""
    rng = np.random.default_rng(seed)
    clist = sorted(candidates)
    rng.shuffle(clist)
    return [(ip, 0.0, {}) for ip in clist]


def fanout_ranking(
    df, suspected_bots: Set[str], onset_times: Dict[str, float],
    victim_ip: Optional[str], pre_window: float = 120.0,
) -> List[Tuple[str, float, dict]]:
    """Baseline: rank by total outbound unique-dst count in pre-window."""
    if not onset_times:
        return []
    min_onset = min(onset_times.values())
    pre = df[(df["timestamp"] >= min_onset - pre_window) & (df["timestamp"] < min_onset)]
    all_ips = set(df["src_ip"].unique()) | set(df["dst_ip"].unique())
    exclude = suspected_bots | ({victim_ip} if victim_ip else set())
    candidates = all_ips - exclude

    scores = {}
    for c in candidates:
        c_flows = pre[pre["src_ip"] == c]
        scores[c] = c_flows["dst_ip"].nunique() if len(c_flows) > 0 else 0

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(ip, float(s), {}) for ip, s in ranked]


def degree_centrality_ranking(
    df, suspected_bots: Set[str], onset_times: Dict[str, float],
    victim_ip: Optional[str], pre_window: float = 120.0,
) -> List[Tuple[str, float, dict]]:
    """Baseline: rank by out-degree centrality in pre-attack graph."""
    import networkx as nx
    from attribution.graph import build_pre_attack_graph

    G = build_pre_attack_graph(df, onset_times, pre_window)
    if not G:
        return []

    all_ips = set(df["src_ip"].unique()) | set(df["dst_ip"].unique())
    exclude = suspected_bots | ({victim_ip} if victim_ip else set())
    candidates = all_ips - exclude

    dc = nx.out_degree_centrality(G)
    ranked = sorted([(c, dc.get(c, 0.0)) for c in candidates],
                    key=lambda x: x[1], reverse=True)
    return [(ip, s, {}) for ip, s in ranked]
