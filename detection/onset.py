"""Per-bot attack onset estimation from detector alerts."""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from detection.detector import Alert


def estimate_onsets(
    df: pd.DataFrame,
    alerts: List[Alert],
    rate_multiplier: float = 3.0,
    micro_window: float = 2.0,
    post_alert_windows: int = 5,
) -> Tuple[Set[str], Dict[str, float], Optional[str]]:
    """Identify suspected bots and estimate each bot's attack onset time.

    Strategy:
    1. Find the suspected victim (most-targeted dst in alert windows).
    2. Find src IPs sending high-rate traffic to the victim ⇒ suspected bots.
    3. For each bot, slide a micro-window backward to find where its rate
       first exceeds rate_multiplier × its pre-alert baseline.

    Returns (suspected_bots, onset_times, victim_ip).
    """
    if not alerts:
        return set(), {}, None

    first_alert = min(alerts, key=lambda a: a.window_start)
    last_alert = max(alerts, key=lambda a: a.window_end)

    # Flows inside alert windows
    alert_start = first_alert.window_start
    alert_end = last_alert.window_end + post_alert_windows * (
        alerts[0].window_end - alerts[0].window_start if alerts else 5.0)
    alert_mask = (df["timestamp"] >= alert_start) & (df["timestamp"] <= alert_end)
    alert_flows = df.loc[alert_mask]

    if alert_flows.empty:
        return set(), {}, None

    # Victim = most common dst in alert windows
    victim_ip = str(alert_flows["dst_ip"].value_counts().index[0])

    # Suspected bots = src IPs sending to victim in alert windows
    to_victim = alert_flows[alert_flows["dst_ip"] == victim_ip]
    bot_flow_counts = to_victim.groupby("src_ip").size()
    # Filter: must have sent more than a handful of flows
    threshold = max(3, bot_flow_counts.median() * 0.3) if len(bot_flow_counts) > 0 else 3
    suspected_bots = set(bot_flow_counts[bot_flow_counts >= threshold].index)

    # Pre-alert baseline rate per bot → victim
    pre_mask = (df["timestamp"] < alert_start) & (df["dst_ip"] == victim_ip)
    pre_flows = df.loc[pre_mask]
    pre_duration = max(alert_start - float(df["timestamp"].min()), 1.0)

    onset_times: Dict[str, float] = {}
    for bot in suspected_bots:
        bot_pre = pre_flows[pre_flows["src_ip"] == bot]
        baseline_rate = len(bot_pre) / pre_duration  # flows/sec

        # All flows from this bot to victim, sorted
        bot_all = df[(df["src_ip"] == bot) & (df["dst_ip"] == victim_ip)].sort_values("timestamp")
        if bot_all.empty:
            continue

        ts = bot_all["timestamp"].values
        # Slide micro-window to find onset
        onset = float(ts[0])
        for i in range(len(ts)):
            t_start = float(ts[i])
            t_end = t_start + micro_window
            n_in_window = int(np.sum((ts >= t_start) & (ts < t_end)))
            window_rate = n_in_window / micro_window
            if window_rate > max(baseline_rate * rate_multiplier, 1.0):
                onset = t_start
                break

        onset_times[bot] = onset

    return suspected_bots, onset_times, victim_ip
