"""Attack traffic generators (UDP flood, SYN flood, HTTP flood).

SAFETY: generates data rows only — no sockets, no real network activity.
"""
from __future__ import annotations
from typing import List
import numpy as np

FlowRecord = dict


def generate_udp_flood(
    rng: np.random.Generator, bot_ip: str, victim_ip: str,
    onset_time: float, duration: float = 100.0,
    flows_per_second: float = 10.0,
) -> List[FlowRecord]:
    """High-rate large UDP packets to random ports on the victim."""
    flows: List[FlowRecord] = []
    t = onset_time
    while t < onset_time + duration:
        pkts = int(rng.integers(50, 200))
        flows.append({
            "timestamp": round(t, 6), "src_ip": bot_ip, "dst_ip": victim_ip,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": int(rng.integers(1, 65536)),
            "protocol": "UDP", "packets": pkts,
            "bytes": int(pkts * int(rng.integers(1000, 1500))),
            "flags": "-", "duration": round(float(rng.exponential(0.2)), 4),
        })
        t += float(rng.exponential(1.0 / flows_per_second))
    return flows


def generate_syn_flood(
    rng: np.random.Generator, bot_ip: str, victim_ip: str,
    onset_time: float, duration: float = 100.0,
    flows_per_second: float = 15.0,
) -> List[FlowRecord]:
    """SYN-only TCP flows — no handshake completion."""
    flows: List[FlowRecord] = []
    t = onset_time
    while t < onset_time + duration:
        flows.append({
            "timestamp": round(t, 6), "src_ip": bot_ip, "dst_ip": victim_ip,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": int(rng.choice([80, 443, 8080, 8443])),
            "protocol": "TCP", "packets": int(rng.integers(1, 3)),
            "bytes": int(rng.integers(40, 80)),
            "flags": "SYN", "duration": 0.0,
        })
        t += float(rng.exponential(1.0 / flows_per_second))
    return flows


def generate_http_flood(
    rng: np.random.Generator, bot_ip: str, victim_ip: str,
    onset_time: float, duration: float = 100.0,
    flows_per_second: float = 8.0,
) -> List[FlowRecord]:
    """Many short but complete HTTP connections — looks legit individually."""
    flows: List[FlowRecord] = []
    t = onset_time
    while t < onset_time + duration:
        pkts = int(rng.integers(5, 20))
        flows.append({
            "timestamp": round(t, 6), "src_ip": bot_ip, "dst_ip": victim_ip,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": int(rng.choice([80, 443])),
            "protocol": "TCP", "packets": pkts,
            "bytes": int(pkts * int(rng.integers(200, 1000))),
            "flags": "SYN SYN-ACK ACK FIN",
            "duration": round(float(rng.exponential(0.3)), 4),
        })
        t += float(rng.exponential(1.0 / flows_per_second))
    return flows
