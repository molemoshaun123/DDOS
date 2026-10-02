# Project Plan — Causal Onset Back-Tracing for DDoS Attribution

> **Status**: DRAFT — awaiting approval before implementation begins.

---

## 1  Problem Statement

Given flow-level network traffic, we must:

1. **Detect** DDoS attacks (volumetric, protocol, application-layer) with low latency.
2. **Attribute** the attack to the most likely botmaster / C2 controller by analysing
   traffic *before* each bot's attack onset.

The novel contribution is **Causal Onset Back-Tracing (COBT)** — a multi-signal
scoring pipeline that fuses temporal, structural, and behavioural evidence to rank
candidate controllers.

---

## 2  Repository Layout

```
DDOS/
├── data_sim/          # Synthetic flow generator + ground-truth labels
│   ├── __init__.py
│   ├── simulator.py   # Main SimulatorConfig + generate() entry-point
│   ├── profiles.py    # Benign host behaviour profiles
│   ├── attacks.py     # Attack-traffic generators (UDP, SYN, HTTP)
│   └── c2.py          # C2-channel generators (centralised, beacon, proxied)
│
├── detection/         # Sliding-window DDoS detector
│   ├── __init__.py
│   ├── features.py    # Per-window feature extraction
│   ├── detector.py    # Entropy + rate + ratio detector → alerts
│   └── onset.py       # Per-bot attack-onset estimation
│
├── attribution/       # COBT scoring pipeline
│   ├── __init__.py
│   ├── temporal.py    # (a) Temporal-precedence scoring
│   ├── fanout.py      # (b) Fan-out synchrony scoring
│   ├── baseline.py    # (c) Baseline-deviation scoring
│   ├── graph.py       # (d) Graph-centrality / star-structure scoring
│   ├── fusion.py      # Adaptive weight fusion across C2 styles
│   └── ranker.py      # Top-level rank(candidates) → sorted list
│
├── pipeline/          # End-to-end integration
│   ├── __init__.py
│   ├── runner.py      # detect → attribute orchestration
│   └── cli.py         # CLI entry-point (argparse)
│
├── evaluation/        # Experiments, metrics, plotting
│   ├── __init__.py
│   ├── metrics.py     # P/R/F1, MRR, Top-K accuracy helpers
│   ├── experiments.py # Experiment configurations + runner
│   └── plots.py       # Matplotlib figure generators
│
├── report/            # Exported figures & LaTeX-friendly tables
│
├── tests/             # Unit tests (pytest)
│   ├── test_simulator.py
│   ├── test_detector.py
│   ├── test_attribution.py
│   └── test_pipeline.py
│
├── docs/
│   ├── PLAN.md         # ← this file
│   └── DESIGN_NOTES.md # Running design-decision log
│
├── requirements.txt
└── README.md
```

---

## 3  Data Simulator Design

### 3.1  Flow Record Schema

Each synthetic flow is a row with columns:

| Column | Type | Description |
|--------|------|-------------|
| `flow_id` | int | Unique identifier |
| `timestamp` | float | Flow start time (seconds from epoch 0) |
| `src_ip` | str | Source IP (synthetic, e.g. `10.x.x.x`) |
| `dst_ip` | str | Destination IP |
| `src_port` | int | Source port |
| `dst_port` | int | Destination port |
| `protocol` | str | `TCP` / `UDP` / `HTTP` |
| `packets` | int | Packet count in the flow |
| `bytes` | int | Byte count |
| `flags` | str | TCP flags summary (`SYN`, `SYN-ACK`, `ACK`, …) or `—` |
| `duration` | float | Flow duration in seconds |
| `label` | str | `benign` / `attack` / `c2` |
| `actor` | str | `background` / `bot` / `botmaster` / `proxy` / `server` |

### 3.2  Traffic Components

1. **Benign background** (configurable host count, ~80 hosts default)
   - Web-browsing profiles (bursts to popular servers, Pareto inter-arrival)
   - DNS queries (small, frequent, to 1–2 DNS resolvers — "popular server" decoy)
   - NTP / update-server traffic (periodic, fan-out-1 — decoy)
   - Peer-to-peer-like chatter (random small flows)

2. **Attack traffic** (injected at configurable onset time)
   - **UDP flood**: high packet-rate UDP from each bot → victim, large packets
   - **SYN flood**: SYN-only TCP from each bot → victim, no completing handshake
   - **HTTP flood**: many short HTTP flows from each bot → victim port 80/443

3. **C2 traffic** (injected *before* attack onset)
   - **Centralised push**: botmaster sends a short command flow to each bot in
     rapid succession, ~delta_t before each bot begins attacking. Jitter on delta_t is
     configurable.
   - **Periodic beacon/poll**: each bot polls the botmaster at regular intervals
     (period P +/- jitter). The "go" command is in the last poll response before
     onset.
   - **Two-tier proxied**: botmaster → proxy tier (1–3 proxies) → bots. Each
     hop adds latency + jitter.

### 3.3  Ground Truth Output

A JSON sidecar file with:
```json
{
  "seed": 42,
  "botmaster_ip": "10.0.0.1",
  "proxy_ips": [],
  "bot_ips": ["10.1.0.1", "10.1.0.2"],
  "victim_ip": "10.99.0.1",
  "attack_type": "syn_flood",
  "c2_style": "centralised",
  "attack_onset_global": 300.0,
  "bot_onsets": {"10.1.0.1": 300.2, "10.1.0.2": 300.5},
  "c2_params": {"jitter_std": 0.5, "pre_attack_window": 60}
}
```

---

## 4  Algorithm Design

### 4.1  Detection — Entropy & Rate Sliding-Window Detector

```
PARAMETERS
  W         = window width (seconds), default 5
  S         = slide step (seconds), default 1
  alpha_entropy = z-score threshold for src-IP entropy drop
  alpha_rate    = z-score threshold for packet-rate spike
  alpha_syn     = threshold for SYN/(SYN+ACK) ratio
  warmup    = number of windows before detector activates

ALGORITHM  DetectDDoS(flows)
  windows <- partition flows into overlapping windows of width W, step S
  history <- empty deque (for running mean/std)

  FOR each window w_i:
    features[i] <- {
      src_entropy  : Shannon entropy of src_ip distribution,
      dst_entropy  : Shannon entropy of dst_ip distribution,
      flow_rate    : count(flows) / W,
      packet_rate  : sum(packets) / W,
      byte_rate    : sum(bytes) / W,
      syn_ratio    : count(SYN-only) / count(TCP) if TCP > 0 else 0,
    }

    IF i > warmup:
      z_entropy <- (mean_hist(src_entropy) - features[i].src_entropy)
                    / std_hist(src_entropy)
      z_rate    <- (features[i].packet_rate - mean_hist(packet_rate))
                    / std_hist(packet_rate)

      alert <- (z_entropy > alpha_entropy) OR
               (z_rate > alpha_rate)    OR
               (features[i].syn_ratio > alpha_syn)

      IF alert:
        emit Alert(window_start, window_end, features[i])

    push features[i] onto history

  RETURN alerts
```

### 4.2  Onset Estimation — Per-Bot Attack Start Time

```
ALGORITHM  EstimateOnsets(flows, alert_time)
  bots <- set of src_ips sending high-rate traffic to the victim
         in the alert window and the next K windows

  FOR each bot b in bots:
    attack_flows <- flows from b to victim, sorted by timestamp
    T0[b] <- first timestamp where a sliding micro-window
             (width 1 s) exceeds 3x b's pre-alert mean rate
             to victim

  RETURN bots, T0
```

### 4.3  Attribution — Causal Onset Back-Tracing (COBT)

```
INPUT
  bots        : set of suspected bot IPs
  T0          : dict bot -> onset timestamp
  flows       : full flow DataFrame
  pre_window  : seconds before min(T0) to analyse (default 120)
  all_hosts   : set of all IPs observed

CANDIDATES <- all_hosts - bots - {victim}

FOR each candidate c in CANDIDATES:
  -- (a) Temporal Precedence -----------------------------------------------
  lags <- []
  FOR each bot b in bots:
    contacts <- flows from c to b with timestamp in
                [T0[b] - pre_window, T0[b]]
    IF contacts not empty:
      best_contact <- contact with max timestamp (closest before T0[b])
      lag <- T0[b] - best_contact.timestamp
      lags.append(lag)

  IF len(lags) >= 2:
    temporal_score[c] <- (len(lags) / len(bots))     # coverage
                        * exp(-std(lags))             # consistency
                        * exp(-mean(lags) / tau)      # recency (tau ~ 30 s)
  ELSE:
    temporal_score[c] <- 0

  -- (b) Fan-out Synchrony ------------------------------------------------
  burst_window <- 10 s
  pre_contacts <- flows from c to any bot in [min(T0)-pre_window, min(T0)]
  IF pre_contacts not empty:
    # slide a burst_window across pre_contacts, find max bots-contacted
    max_burst_fanout <- max over slides of |unique dst_ip intersection bots|
    fanout_score[c]  <- max_burst_fanout / len(bots)
  ELSE:
    fanout_score[c] <- 0

  -- (c) Baseline Deviation -----------------------------------------------
  normal_window <- flows from c in [0, min(T0) - pre_window]
  normal_fanout_rate <- |unique dst per 60 s window| averaged
  pre_attack_fanout_rate <- |unique dst in pre_window| / (pre_window / 60)

  IF normal_fanout_rate > 0:
    deviation_score[c] <- (pre_attack_fanout_rate - normal_fanout_rate)
                           / normal_fanout_rate
    deviation_score[c] <- max(deviation_score[c], 0)   # clamp
  ELSE:
    deviation_score[c] <- pre_attack_fanout_rate  # no baseline -> raw

  -- (d) Graph Centrality -------------------------------------------------
  G <- directed graph of host interactions in pre-attack window
       edge weight = flow count
  # Compute "star score": out-degree to bots / total out-degree
  star_score[c] <- out_degree_to_bots(c, G) / max(out_degree(c, G), 1)
  # Also use betweenness centrality as secondary signal
  betweenness[c] <- betweenness_centrality(G)[c]
  graph_score[c] <- 0.7 * star_score[c] + 0.3 * betweenness[c]

-- Adaptive Fusion ---------------------------------------------------------
# Detect C2 style from evidence patterns, then weight accordingly
style <- infer_c2_style(temporal_scores, fanout_scores, bots, flows)

weights <- {
  'centralised': [0.30, 0.30, 0.15, 0.25],  # temporal, fanout, deviation, graph
  'beacon':      [0.40, 0.15, 0.25, 0.20],
  'proxied':     [0.15, 0.20, 0.25, 0.40],  # graph matters more
}[style]

FOR each candidate c:
  final_score[c] <- weights[0] * norm(temporal_score[c])
                  + weights[1] * norm(fanout_score[c])
                  + weights[2] * norm(deviation_score[c])
                  + weights[3] * norm(graph_score[c])

RETURN sorted(CANDIDATES, key=final_score, descending)
```

#### C2 Style Inference Heuristic

```
ALGORITHM  infer_c2_style(temporal_scores, fanout_scores, bots, flows)
  top_candidates <- top-5 by temporal_score

  # Check for "burst" signature -> centralised
  IF any candidate has fanout_score > 0.6:
    RETURN 'centralised'

  # Check for periodic contact pattern -> beacon
  FOR each top candidate c:
    contacts <- flows from c to any bot, sorted by time
    IF len(contacts) > 4:
      intervals <- diff(timestamps)
      IF coefficient_of_variation(intervals) < 0.3:
        RETURN 'beacon'

  # Check for two-hop structure -> proxied
  FOR each top candidate c:
    IF c contacted < 30% of bots directly BUT
       hosts contacted by c in turn contacted > 60% of bots:
      RETURN 'proxied'

  RETURN 'centralised'   # default fallback
```

### 4.4  Normalisation

All four component scores are min-max normalised across candidates
within each run to [0, 1] before fusion.

---

## 5  Experiment Plan

### 5.1  Detection Experiments

| ID | Variable | Levels | Metrics |
|----|----------|--------|---------|
| D1 | Attack type | UDP, SYN, HTTP | Precision, Recall, F1, FPR, Detection delay |
| D2 | Bot count | 5, 10, 20, 50 | Same |
| D3 | Window size W | 2, 5, 10 s | Same |
| D4 | Noise level (benign host count) | 40, 80, 160 | Same |

### 5.2  Attribution Experiments

| ID | Variable | Levels | Metrics |
|----|----------|--------|---------|
| A1 | C2 style | centralised, beacon, proxied | Top-1, Top-3, Top-5 acc, MRR |
| A2 | Bot count | 5, 10, 20, 50 | Same |
| A3 | C2 jitter std | 0.1, 0.5, 1.0, 2.0, 5.0 s | Same |
| A4 | Noise level | 40, 80, 160 hosts | Same |
| A5 | Attack type x C2 style | 3 x 3 | Same |

### 5.3  Baseline Comparisons (for Attribution)

| Baseline | Description |
|----------|-------------|
| B1 — Random | Random ranking of candidates |
| B2 — Fan-out | Rank by total outbound unique-dst count in pre-window |
| B3 — Degree centrality | Rank by out-degree centrality in pre-attack graph |
| COBT (ours) | Full pipeline |

### 5.4  Ablation Study

| Variant | Removed component |
|---------|-------------------|
| COBT-a | No temporal precedence |
| COBT-b | No fan-out synchrony |
| COBT-c | No baseline deviation |
| COBT-d | No graph score |

### 5.5  Limitation / Failure-Case Experiments

| ID | Scenario | Expected outcome |
|----|----------|------------------|
| L1 | Very high jitter (std = 10 s) | Attribution degrades — temporal signal is washed out |
| L2 | Multi-hop proxied C2 (3 tiers) | Top-1 finds proxy, not botmaster; Top-5 may miss |
| L3 | Botmaster goes idle well before attack (gap > 120 s) | Pre-window misses C2 traffic entirely |
| L4 | Botmaster also acts as a benign popular server | Baseline-deviation score suppressed; harder to rank |

---

## 6  Implementation Order & Milestones

| Stage | Deliverable | Pause? |
|-------|-------------|--------|
| **0** | This plan + DESIGN_NOTES.md | **YES — wait for approval** |
| **1** | `data_sim/` — simulator + ground truth + unit tests | YES |
| **2** | `detection/` — detector + onset estimator + tests | YES |
| **3** | `attribution/` — COBT scoring pipeline + tests | YES |
| **4** | `pipeline/` + CLI integration | YES |
| **5** | `evaluation/` — experiments + plots + report/ figures | YES |

---

## 7  Dependencies

```
numpy>=1.24
pandas>=2.0
scipy>=1.10
networkx>=3.0
matplotlib>=3.7
seaborn>=0.12
pytest>=7.0
```

No ML frameworks (scikit-learn, torch) needed — the detector is purely
statistical and the attribution is a hand-crafted scoring pipeline.

---

## 8  Reproducibility

- All random generators seeded via a single `MASTER_SEED` passed through the CLI.
- Every experiment logs its config and seed to a JSON file alongside results.
- Figures saved as both PNG (300 dpi) and PDF.
