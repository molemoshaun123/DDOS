"""C2 channel traffic generators (centralised, beacon, proxied).

SAFETY: generates data rows only — no sockets, no real network activity.
"""
from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np

FlowRecord = dict


def _c2_flow(ts: float, src: str, dst: str, rng: np.random.Generator) -> FlowRecord:
    """Single small C2 command/response flow."""
    return {
        "timestamp": round(ts, 6), "src_ip": src, "dst_ip": dst,
        "src_port": int(rng.integers(1024, 65536)),
        "dst_port": int(rng.choice([443, 8443, 4444, 6667, 53])),
        "protocol": "TCP", "packets": int(rng.integers(2, 6)),
        "bytes": int(rng.integers(100, 500)),
        "flags": "SYN SYN-ACK ACK FIN",
        "duration": round(float(rng.exponential(0.1)), 4),
    }


def generate_centralised_c2(
    rng: np.random.Generator, botmaster_ip: str, bot_ips: List[str],
    bot_onsets: Dict[str, float], jitter_std: float = 0.5,
    command_lead_time: float = 5.0, multi_flow: bool = True,
) -> Tuple[List[FlowRecord], Dict[str, float]]:
    """Centralised push: botmaster → bots in rapid succession before onset."""
    flows: List[FlowRecord] = []
    contacts: Dict[str, float] = {}
    for bot_ip in bot_ips:
        if bot_ip not in bot_onsets:
            continue
        lead = max(0.5, command_lead_time + rng.normal(0, jitter_std))
        cmd_t = bot_onsets[bot_ip] - lead
        flows.append(_c2_flow(cmd_t, botmaster_ip, bot_ip, rng))
        contacts[bot_ip] = cmd_t
        if multi_flow and rng.random() > 0.4:
            for _ in range(int(rng.integers(1, 3))):
                et = cmd_t + float(rng.exponential(0.3))
                flows.append(_c2_flow(et, botmaster_ip, bot_ip, rng))
    return flows, contacts


def generate_beacon_c2(
    rng: np.random.Generator, botmaster_ip: str, bot_ips: List[str],
    bot_onsets: Dict[str, float], beacon_period: float = 10.0,
    jitter_std: float = 0.5, pre_window: float = 60.0,
    multi_flow: bool = True,
) -> Tuple[List[FlowRecord], Dict[str, float]]:
    """Periodic beacon: bots poll botmaster; last poll carries the go command."""
    flows: List[FlowRecord] = []
    contacts: Dict[str, float] = {}
    for bot_ip in bot_ips:
        if bot_ip not in bot_onsets:
            continue
        onset = bot_onsets[bot_ip]
        t = onset - pre_window + rng.uniform(0, beacon_period)
        last = None
        while t < onset:
            flows.append(_c2_flow(t, bot_ip, botmaster_ip, rng))
            resp_t = t + float(rng.exponential(0.05))
            flows.append(_c2_flow(resp_t, botmaster_ip, bot_ip, rng))
            last = resp_t
            if multi_flow and rng.random() > 0.7:
                et = resp_t + float(rng.exponential(0.1))
                flows.append(_c2_flow(et, botmaster_ip, bot_ip, rng))
                last = et
            t += max(1.0, beacon_period + rng.normal(0, jitter_std))
        if last is not None:
            contacts[bot_ip] = last
    return flows, contacts


def generate_proxied_c2(
    rng: np.random.Generator, botmaster_ip: str, proxy_ips: List[str],
    bot_ips: List[str], bot_onsets: Dict[str, float],
    jitter_std: float = 0.5, hop_delay: float = 2.0,
    multi_flow: bool = True,
) -> Tuple[List[FlowRecord], Dict[str, float]]:
    """Two-tier proxied: botmaster → proxies → bots."""
    flows: List[FlowRecord] = []
    contacts: Dict[str, float] = {}
    if not proxy_ips:
        proxy_ips = ["10.0.1.1"]
    responding = [b for b in bot_ips if b in bot_onsets]
    proxy_to_bots: Dict[str, List[str]] = {p: [] for p in proxy_ips}
    for i, b in enumerate(responding):
        proxy_to_bots[proxy_ips[i % len(proxy_ips)]].append(b)

    for proxy_ip, pbots in proxy_to_bots.items():
        if not pbots:
            continue
        earliest = min(bot_onsets[b] for b in pbots)
        cmd_t = earliest - 2 * hop_delay - abs(rng.normal(0, jitter_std))
        flows.append(_c2_flow(cmd_t, botmaster_ip, proxy_ip, rng))
        if multi_flow and rng.random() > 0.5:
            flows.append(_c2_flow(cmd_t + float(rng.exponential(0.2)),
                                  botmaster_ip, proxy_ip, rng))
        for bot_ip in pbots:
            rd = max(0.3, hop_delay + rng.normal(0, jitter_std * 0.5))
            rt = cmd_t + rd
            flows.append(_c2_flow(rt, proxy_ip, bot_ip, rng))
            contacts[bot_ip] = rt
            if multi_flow and rng.random() > 0.6:
                flows.append(_c2_flow(rt + float(rng.exponential(0.15)),
                                      proxy_ip, bot_ip, rng))
    return flows, contacts
