# Design Notes — COBT DDoS Attribution System

> This document records every design decision and its justification.
> Updated as the project evolves.

---

## Decision Log

### DN-001: Pure statistical detector, no ML (2026-10-02)

**Decision**: Use an entropy + rate + SYN-ratio sliding-window detector instead of
a trained ML classifier.

**Justification**:
- The assignment calls for novelty in the *attribution* stage, not in detection.
  A well-understood statistical detector is simpler to explain, debug, and tune.
- It avoids the need for labelled training data, which would complicate the
  synthetic-data pipeline (train/test split concerns, overfitting to our own
  simulator).
- Sliding-window z-score detection is lightweight and interpretable — easy to
  defend in a presentation.
- Shannon entropy of source IPs is a proven DDoS signal: during an attack,
  traffic converges on one victim, so destination-IP entropy drops and per-source
  flow rate spikes.

---

### DN-002: Four-component COBT scoring (2026-10-02)

**Decision**: Use four independent scoring components fused with adaptive weights
rather than a single monolithic score.

**Justification**:
- Modularity allows ablation experiments (required by the assignment).
- Different C2 architectures leave different forensic footprints; no single
  feature is universal.  Temporal precedence dominates for beacon C2, fan-out
  dominates for centralised push, graph structure dominates for proxied C2.
- Adaptive weighting (infer style first, then adjust weights) is the key novelty
  claim: it lets the system adapt without supervised training.

---

### DN-003: Adaptive weights via heuristic C2-style inference (2026-10-02)

**Decision**: Infer C2 style from evidence patterns (burst → centralised,
periodic intervals → beacon, indirect reachability → proxied) and select
pre-defined weight vectors accordingly.

**Justification**:
- A fully learned weighting would need a training set of labelled attacks, which
  defeats the purpose of an unsupervised attribution method.
- Three discrete style categories are sufficient for the scope of this project
  and are directly testable.
- The inference heuristic is itself a contribution: it shows the system can
  reason about *how* the botnet was commanded, not just *who* commanded it.

**Risk**: The heuristic may misclassify C2 style in noisy conditions. We mitigate
this by making the weight differences moderate (not extreme), so mis-classification
degrades but does not catastrophically fail.

---

### DN-004: Synthetic-only data (2026-10-02)

**Decision**: Build a pure-Python flow-level traffic simulator rather than using
real packet captures.

**Justification**:
- Full control over ground truth (we know exactly which IP is the botmaster).
- Parameterised scenarios for sensitivity experiments (jitter, bot count, noise).
- No ethical or legal concerns about running attack tooling.
- Real datasets (CIC-DDoS2019) label attack vs. benign but rarely label the
  C2 controller — they are useful for detection validation but not for
  attribution evaluation.

**Trade-off**: Synthetic traffic lacks the complexity of real networks (NAT,
middleboxes, encrypted payloads). We acknowledge this in the limitations section.

---

### DN-005: Graph component uses star-structure + betweenness (2026-10-02)

**Decision**: Combine a "star score" (fraction of a node's out-edges going to
bots) with betweenness centrality, weighted 70/30.

**Justification**:
- Pure betweenness centrality would rank high-traffic routers or DNS servers
  highly — the star score corrects for this by focusing on *bot-directed* edges.
- Betweenness adds value for proxied C2 where the proxy node sits on many
  shortest paths between the botmaster and bots.
- 70/30 weighting is a design choice; can be tuned in future work.

---

### DN-006: Min-max normalisation per run (2026-10-02)

**Decision**: Normalise each component score to [0, 1] across all candidates
within a single run before fusion.

**Justification**:
- Component scores have different natural scales (e.g., temporal score uses
  exponentials ∈ [0, 1], fan-out is a ratio ∈ [0, 1], deviation can be
  unbounded). Min-max makes the weights interpretable.
- Per-run normalisation means the system adapts to the range of each specific
  scenario rather than relying on global calibration.

---

*More decisions will be added as implementation proceeds.*
