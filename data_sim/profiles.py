"""
Benign host traffic profiles for the synthetic flow simulator.

Each function generates a list of flow records (dicts) for a single host
over a time interval.  Flow records contain only observable network
metadata — no labels or ground-truth information.

SAFETY: This module generates data rows only — no sockets, no packets,
no real network activity.
"""

from __future__ import annotations

from typing import List

import numpy as np

# ---------------------------------------------------------------------------
# Type alias – each flow record is a plain dict that becomes a DataFrame row
# ---------------------------------------------------------------------------
FlowRecord = dict


# ======================================================================
#  Regular-host traffic profiles
# ======================================================================

def generate_web_browsing(
    rng: np.random.Generator,
    host_ip: str,
    servers: List[str],
    t_start: float,
    t_end: float,
    mean_session_gap: float = 30.0,
) -> List[FlowRecord]:
    """Generate web-browsing flows with bursty, heavy-tailed arrivals.

    Model
    -----
    Sessions of 3–10 HTTPS requests to a randomly chosen popular server,
    separated by Pareto-distributed idle periods (heavy tail ≈ human
    think-time).
    """
    flows: List[FlowRecord] = []
    t = t_start + rng.exponential(mean_session_gap / 2)

    while t < t_end:
        server = str(rng.choice(servers))
        n_requests = int(rng.integers(3, 11))

        for _ in range(n_requests):
            if t >= t_end:
                break
            src_port = int(rng.integers(1024, 65536))
            duration = round(float(rng.exponential(0.5)), 4)
            packets = int(rng.integers(5, 30))
            nbytes = int(packets * int(rng.integers(200, 1500)))

            flows.append({
                "timestamp": round(t, 6),
                "src_ip": host_ip,
                "dst_ip": server,
                "src_port": src_port,
                "dst_port": 443,
                "protocol": "TCP",
                "packets": packets,
                "bytes": nbytes,
                "flags": "SYN SYN-ACK ACK FIN",
                "duration": duration,
            })
            # Small gap within a browsing burst
            t += float(rng.exponential(0.3))

        # Heavy-tailed inter-session gap
        t += float(rng.pareto(1.5) * mean_session_gap * 0.3)

    return flows


def generate_dns_queries(
    rng: np.random.Generator,
    host_ip: str,
    dns_servers: List[str],
    t_start: float,
    t_end: float,
    mean_interval: float = 5.0,
) -> List[FlowRecord]:
    """Generate periodic DNS query flows (UDP to port 53).

    Model
    -----
    Small UDP queries at roughly regular intervals with exponential
    jitter, to one of the configured resolvers.
    """
    flows: List[FlowRecord] = []
    t = t_start + rng.exponential(mean_interval)

    while t < t_end:
        server = str(rng.choice(dns_servers))
        flows.append({
            "timestamp": round(t, 6),
            "src_ip": host_ip,
            "dst_ip": server,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": 53,
            "protocol": "UDP",
            "packets": int(rng.integers(1, 3)),
            "bytes": int(rng.integers(60, 200)),
            "flags": "-",
            "duration": round(float(rng.exponential(0.01)), 4),
        })
        t += float(rng.exponential(mean_interval))

    return flows


def generate_ntp_sync(
    rng: np.random.Generator,
    host_ip: str,
    ntp_server: str,
    t_start: float,
    t_end: float,
    period: float = 64.0,
) -> List[FlowRecord]:
    """Generate periodic NTP synchronisation flows (UDP port 123).

    Model
    -----
    Standard ntpd poll interval (~64 s) with small Gaussian jitter.
    """
    flows: List[FlowRecord] = []
    t = t_start + rng.uniform(0, period)

    while t < t_end:
        flows.append({
            "timestamp": round(t, 6),
            "src_ip": host_ip,
            "dst_ip": ntp_server,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": 123,
            "protocol": "UDP",
            "packets": 2,
            "bytes": int(rng.integers(90, 120)),
            "flags": "-",
            "duration": round(float(rng.exponential(0.05)), 4),
        })
        t += period + float(rng.normal(0, period * 0.05))

    return flows


def generate_p2p_chatter(
    rng: np.random.Generator,
    host_ip: str,
    peers: List[str],
    t_start: float,
    t_end: float,
    mean_interval: float = 20.0,
) -> List[FlowRecord]:
    """Generate small peer-to-peer-like flows to random peers.

    Model
    -----
    Occasional small TCP/UDP flows representing file-sharing, messaging,
    or other background applications.
    """
    flows: List[FlowRecord] = []
    if not peers:
        return flows

    t = t_start + rng.exponential(mean_interval)

    while t < t_end:
        peer = str(rng.choice(peers))
        proto = str(rng.choice(["TCP", "UDP"]))
        flags = "SYN SYN-ACK ACK FIN" if proto == "TCP" else "-"
        flows.append({
            "timestamp": round(t, 6),
            "src_ip": host_ip,
            "dst_ip": peer,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": int(rng.integers(1024, 65536)),
            "protocol": proto,
            "packets": int(rng.integers(2, 15)),
            "bytes": int(rng.integers(100, 2000)),
            "flags": flags,
            "duration": round(float(rng.exponential(1.0)), 4),
        })
        t += float(rng.exponential(mean_interval))

    return flows


# ======================================================================
#  Decoy / infrastructure host profiles
#
#  These hosts are BENIGN but exhibit high fan-out or periodic contact
#  patterns that can confuse an attribution system into ranking them as
#  candidate C2 controllers.  They are critical for realistic testing.
# ======================================================================

def generate_admin_workstation(
    rng: np.random.Generator,
    admin_ip: str,
    managed_hosts: List[str],
    t_start: float,
    t_end: float,
    mean_interval: float = 15.0,
) -> List[FlowRecord]:
    """Generate admin workstation traffic — SSH/management to many hosts.

    Why this is a decoy
    -------------------
    The admin connects to many hosts (including some that happen to be
    bot IPs), creating a fan-out pattern that superficially resembles C2
    command distribution.
    """
    flows: List[FlowRecord] = []
    t = t_start + rng.exponential(mean_interval)

    while t < t_end:
        target = str(rng.choice(managed_hosts))
        dst_port = int(rng.choice([22, 22, 22, 3389, 8080, 443]))
        duration = round(float(rng.exponential(5.0)), 4)
        packets = int(rng.integers(10, 100))
        nbytes = int(packets * int(rng.integers(100, 800)))

        flows.append({
            "timestamp": round(t, 6),
            "src_ip": admin_ip,
            "dst_ip": target,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": dst_port,
            "protocol": "TCP",
            "packets": packets,
            "bytes": nbytes,
            "flags": "SYN SYN-ACK ACK FIN",
            "duration": duration,
        })
        t += float(rng.exponential(mean_interval))

    return flows


def generate_monitoring_server(
    rng: np.random.Generator,
    monitor_ip: str,
    monitored_hosts: List[str],
    t_start: float,
    t_end: float,
    check_period: float = 30.0,
) -> List[FlowRecord]:
    """Generate monitoring / health-check flows to all managed hosts.

    Why this is a decoy
    -------------------
    Sends regular small health checks to *every* host in the network,
    creating high fan-out that resembles C2 command distribution.  The
    periodicity also mimics a beacon-style C2 polling pattern.
    """
    flows: List[FlowRecord] = []
    t = t_start + rng.uniform(0, check_period)

    while t < t_end:
        # Each cycle, probe 50-100 % of hosts (some randomness)
        n_probes = max(1, int(len(monitored_hosts) * rng.uniform(0.5, 1.0)))
        targets = rng.choice(
            monitored_hosts,
            size=min(n_probes, len(monitored_hosts)),
            replace=False,
        )
        for target in targets:
            flows.append({
                "timestamp": round(t + float(rng.exponential(0.1)), 6),
                "src_ip": monitor_ip,
                "dst_ip": str(target),
                "src_port": int(rng.integers(1024, 65536)),
                "dst_port": int(rng.choice([80, 443, 8443, 9090])),
                "protocol": "TCP",
                "packets": int(rng.integers(3, 8)),
                "bytes": int(rng.integers(200, 600)),
                "flags": "SYN SYN-ACK ACK FIN",
                "duration": round(float(rng.exponential(0.1)), 4),
            })
        t += check_period + float(rng.normal(0, check_period * 0.1))

    return flows


def generate_update_pusher(
    rng: np.random.Generator,
    server_ip: str,
    client_hosts: List[str],
    t_start: float,
    t_end: float,
    push_interval: float = 120.0,
) -> List[FlowRecord]:
    """Generate software-update push flows to random host subsets.

    Why this is a decoy
    -------------------
    Periodically pushes updates to 10–40 % of hosts, creating occasional
    burst fan-out that resembles a centralised C2 push.
    """
    flows: List[FlowRecord] = []
    t = t_start + rng.uniform(0, push_interval)

    while t < t_end:
        n_targets = max(1, int(len(client_hosts) * rng.uniform(0.1, 0.4)))
        targets = rng.choice(
            client_hosts,
            size=min(n_targets, len(client_hosts)),
            replace=False,
        )
        for target in targets:
            flows.append({
                "timestamp": round(t + float(rng.exponential(0.5)), 6),
                "src_ip": server_ip,
                "dst_ip": str(target),
                "src_port": int(rng.integers(1024, 65536)),
                "dst_port": int(rng.choice([443, 8443])),
                "protocol": "TCP",
                "packets": int(rng.integers(20, 100)),
                "bytes": int(rng.integers(5000, 50000)),
                "flags": "SYN SYN-ACK ACK FIN",
                "duration": round(float(rng.exponential(2.0)), 4),
            })
        t += push_interval + float(rng.normal(0, push_interval * 0.1))

    return flows


def generate_load_balancer(
    rng: np.random.Generator,
    lb_ip: str,
    backend_hosts: List[str],
    t_start: float,
    t_end: float,
    mean_interval: float = 2.0,
) -> List[FlowRecord]:
    """Generate load-balancer forwarding flows to backend servers.

    Why this is a decoy
    -------------------
    Continuously distributes incoming traffic across back-end hosts
    (some of which may be bot IPs), producing sustained high fan-out.
    """
    flows: List[FlowRecord] = []
    if not backend_hosts:
        return flows

    t = t_start + rng.exponential(mean_interval)

    while t < t_end:
        target = str(rng.choice(backend_hosts))
        flows.append({
            "timestamp": round(t, 6),
            "src_ip": lb_ip,
            "dst_ip": target,
            "src_port": int(rng.integers(1024, 65536)),
            "dst_port": int(rng.choice([80, 443, 8080])),
            "protocol": "TCP",
            "packets": int(rng.integers(4, 20)),
            "bytes": int(rng.integers(500, 5000)),
            "flags": "SYN SYN-ACK ACK FIN",
            "duration": round(float(rng.exponential(0.3)), 4),
        })
        t += float(rng.exponential(mean_interval))

    return flows
