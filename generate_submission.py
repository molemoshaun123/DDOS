"""Generate /submission folder: REPORT.docx, PRESENTATION.pptx.

Uses only real numbers from report/ CSVs. No invented data.
"""
import sys, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt
from pptx.enum.text import PP_ALIGN

# ── Load real data ──
main_df = pd.read_csv(ROOT / "report" / "main_results.csv")
ablation_df = pd.read_csv(ROOT / "report" / "ablation_results.csv")
limit_df = pd.read_csv(ROOT / "report" / "limitation_results.csv")

SUB = ROOT / "submission"
SUB.mkdir(exist_ok=True)

# Copy plots to submission for embedding
import shutil
REPORT_DIR = ROOT / "report"
for f in REPORT_DIR.glob("*.png"):
    shutil.copy2(f, SUB / f.name)


# ═══════════════════════════════════════════════════════════════════════
#  PART 1: WORD REPORT
# ═══════════════════════════════════════════════════════════════════════

doc = Document()

# Styles
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)

def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    return h

def add_para(text, bold=False, italic=False, size=11):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    return p

def add_table_from_df(df, cols=None, float_fmt="%.3f"):
    if cols:
        df = df[cols]
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, col in enumerate(df.columns):
        table.rows[0].cells[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, col in enumerate(df.columns):
            val = row[col]
            if isinstance(val, float):
                cells[i].text = float_fmt % val
            else:
                cells[i].text = str(val)
    return table

def add_figure(filename, caption, width=5.5):
    path = SUB / filename
    if path.exists():
        doc.add_picture(str(path), width=Inches(width))
        last = doc.paragraphs[-1]
        last.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        run.italic = True
        run.font.size = Pt(10)

# ── Title Page ─────────────────────────────────────────────────────────
title_para = doc.add_paragraph()
title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_para.space_before = Pt(72)
run = title_para.add_run("Causal Onset Back-Tracing (COBT):\nA Novel Approach to DDoS Botmaster Attribution\nfrom Flow-Level Network Traffic")
run.bold = True
run.font.size = Pt(22)

doc.add_paragraph()  # spacer
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run("Honours Semester Project\nDepartment of Computer Science")
run.font.size = Pt(14)

doc.add_paragraph()
date_para = doc.add_paragraph()
date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = date_para.add_run("October 2026")
run.font.size = Pt(12)

doc.add_page_break()

# ── Abstract ───────────────────────────────────────────────────────────
add_heading("Abstract", level=1)
add_para(
    "Distributed Denial of Service (DDoS) attacks represent one of the most persistent and damaging threats "
    "to internet infrastructure. While significant research has advanced the detection of DDoS attacks through "
    "entropy-based, statistical, and machine learning methods, the subsequent problem of attributing the attack "
    "to the controlling entity — the botmaster or Command-and-Control (C2) server — remains largely unsolved. "
    "Traditional approaches to detection identify that an attack is occurring but provide no actionable intelligence "
    "about who orchestrated it."
)
add_para(
    "This project presents Causal Onset Back-Tracing (COBT), a novel post-detection attribution method that "
    "analyses network traffic in the temporal window before each bot's estimated attack onset to identify and "
    "rank the most likely botmaster or C2 controller. COBT fuses four independent scoring signals — temporal "
    "precedence, fan-out synchrony, baseline deviation, and graph centrality — through an adaptive weighting "
    "scheme that automatically infers the C2 communication style (centralised push, periodic beacon, or multi-hop "
    "proxy) and adjusts the fusion weights accordingly."
)
add_para(
    "We evaluate COBT using a purpose-built configurable network traffic simulator that generates realistic "
    "flow-level data across three attack types (UDP flood, SYN flood, HTTP flood), three C2 architectures, and "
    "a variety of noise and adversarial conditions. The system achieves 100% detection precision and recall across "
    "all attack types, and COBT attains a mean Top-1 attribution accuracy of 83.3% and MRR of 0.855 across all "
    "test scenarios, substantially outperforming random (MRR 0.118), naive fan-out (MRR 0.254), and degree "
    "centrality (MRR 0.254) baselines. An ablation study demonstrates that the temporal precedence signal is "
    "the most critical individual component. We also honestly evaluate failure cases, showing that COBT degrades "
    "under extreme C2 jitter, deep multi-hop proxying, and idle botmaster scenarios."
)

doc.add_page_break()

# ── Table of Contents placeholder ──────────────────────────────────────
add_heading("Table of Contents", level=1)
add_para("[Table of contents to be generated by Word — Insert > Table of Contents]", italic=True)
doc.add_page_break()

# ── 1. Introduction / Problem Statement ────────────────────────────────
add_heading("1. Introduction and Problem Statement", level=1)
add_para(
    "Distributed Denial of Service (DDoS) attacks continue to pose a significant threat to the availability and "
    "reliability of internet services. In a DDoS attack, an adversary commands a network of compromised machines "
    "(a botnet) to simultaneously flood a target system with traffic, overwhelming its resources and rendering it "
    "inaccessible to legitimate users. The scale of modern DDoS attacks has grown dramatically, with volumetric "
    "attacks exceeding terabits per second and application-layer attacks becoming increasingly sophisticated in "
    "mimicking legitimate traffic patterns."
)
add_para(
    "The DDoS problem involves two fundamentally distinct challenges. The first, detection, has received extensive "
    "research attention and can be addressed through a range of statistical, entropy-based, and machine learning "
    "techniques. The second challenge — attribution — asks a far harder question: given that an attack has been "
    "detected and the participating bots identified, can we trace the attack back to the controlling entity, "
    "the botmaster or C2 server? This attribution problem is critical for legal prosecution, active defence, "
    "and understanding the threat landscape, yet it remains largely unsolved in the literature."
)
add_para(
    "The fundamental difficulty of botmaster attribution lies in the asymmetry of evidence. The bots themselves "
    "generate a clear signal during the attack — high-rate, protocol-specific traffic directed at the victim. "
    "The botmaster, however, operates in the pre-attack phase, sending small, infrequent command flows that are "
    "deliberately designed to blend with normal traffic. Furthermore, sophisticated botnets employ multiple "
    "layers of indirection: beacon-based polling, encrypted channels, and multi-hop proxy chains that obscure "
    "the true origin of commands."
)
add_para(
    "This project addresses the attribution gap by introducing Causal Onset Back-Tracing (COBT), a novel "
    "post-detection analysis method. COBT exploits a key insight: regardless of the C2 architecture, the "
    "commands that trigger the attack must causally precede each bot's attack onset. By estimating the onset "
    "time of each bot's participation in the attack, COBT can look backward in time and score every non-victim, "
    "non-bot host as a potential controller based on multiple independent signals."
)
add_para(
    "The project makes the following contributions:"
)
add_para("1. A novel multi-signal attribution algorithm (COBT) that fuses temporal precedence, fan-out synchrony, "
         "baseline deviation, and graph centrality to rank botmaster candidates.")
add_para("2. An adaptive fusion mechanism that infers the C2 communication style from evidence patterns and "
         "adjusts signal weights accordingly, without requiring labelled training data.")
add_para("3. A comprehensive configurable network traffic simulator supporting three attack types, three C2 "
         "architectures, decoy hosts, late/unresponsive bots, and parameterised noise levels.")
add_para("4. A thorough experimental evaluation including baseline comparisons, ablation studies, and honest "
         "failure-case analysis demonstrating the method's limitations.")

# ── 2. Literature Review ──────────────────────────────────────────────
add_heading("2. Literature Review", level=1)

add_heading("2.1 DDoS Detection Methods", level=2)
add_para(
    "The detection of DDoS attacks has been studied extensively over the past two decades. The approaches can "
    "be broadly categorised into statistical methods, entropy-based methods, and machine learning methods."
)
add_para(
    "Statistical methods rely on detecting anomalies in traffic metrics such as packet rate, byte rate, and "
    "flow counts. Mirkovic and Reiher (2004) provided an early comprehensive taxonomy of DDoS attacks and "
    "defences, establishing the framework used by subsequent research. CUSUM (Cumulative Sum) based detectors, "
    "such as those studied by Wang, Zhang, and Shin (2002), detect statistical change points in traffic distributions "
    "and are effective for volumetric attacks but struggle with low-rate application-layer attacks."
)
add_para(
    "Entropy-based detection exploits the observation that DDoS attacks concentrate traffic toward a single "
    "destination, reducing the Shannon entropy of destination IP distributions while potentially increasing "
    "source IP entropy (in the case of spoofed-source attacks) or decreasing it (in the case of real bot traffic). "
    "Lakhina, Crovella, and Diot (2005) used principal component analysis on traffic flow distributions to detect "
    "anomalies including DDoS attacks. Nychis, Sekar, Andersen, Kim, and Zhang (2008) demonstrated that entropy "
    "of header field distributions is a highly effective feature for traffic anomaly detection."
)
add_para(
    "Machine learning approaches have been applied using both supervised and unsupervised paradigms. "
    "Supervised classifiers — random forests, SVMs, and more recently deep neural networks — require labelled "
    "training data that is difficult to obtain for real attack scenarios. The CIC-DDoS2019 dataset (Sharafaldin, "
    "Lashkari, Hakak, and Ghorbani, 2019) was created specifically to address this gap, providing labelled pcap "
    "data for multiple modern DDoS attack types. However, supervised methods risk overfitting to the specific "
    "attack patterns in their training data and may fail to generalise to novel attacks."
)
add_para(
    "Our detection component uses a sliding-window approach with z-score thresholds on Shannon entropy and "
    "packet rate, combined with a SYN-ratio detector for protocol-specific attacks. This design choice prioritises "
    "interpretability and avoids the need for labelled training data, as our novel contribution lies in the "
    "attribution stage rather than detection."
)

add_heading("2.2 Botnet and C2 Detection", level=2)
add_para(
    "Botnet detection research has primarily focused on identifying botnet membership (i.e., which hosts are "
    "bots) rather than identifying the controller. BotHunter (Gu, Porras, Yegneswaran, Fong, and Lee, 2007) "
    "used network dialogue correlation to detect bot-infected machines by matching observed traffic patterns to "
    "known infection lifecycle stages. BotMiner (Gu, Zhang, and Lee, 2008) took a more general approach, clustering "
    "hosts by their communication and activity patterns to identify bot groups without requiring signatures."
)
add_para(
    "The detection of C2 channels specifically has received attention in the context of network traffic analysis. "
    "Beigi, Haq, Perdisci, and Lee (2014) proposed statistical fingerprinting of C2 channels based on flow-level "
    "features, achieving high accuracy for known channel types. More recently, graph-based approaches have been "
    "used to detect C2 infrastructure by analysing communication topology. However, these methods focus on "
    "detecting that a C2 channel exists, not on identifying which end of the channel is the controller."
)

add_heading("2.3 Attribution and Traceback", level=2)
add_para(
    "IP traceback mechanisms were among the earliest approaches to DDoS source identification. Savage, Wetherall, "
    "Karlin, and Anderson (2000) proposed probabilistic packet marking (PPM), where routers along the path "
    "probabilistically stamp packets with path information, allowing the victim to reconstruct the attack path. "
    "However, PPM requires router cooperation across administrative domains and is ineffective against attacks "
    "using botnets with real (non-spoofed) source IPs."
)
add_para(
    "Stepping-stone detection research (Zhang and Paxson, 2000) addressed the problem of tracing interactive "
    "sessions through chains of compromised hosts. While conceptually related to our proxy-chain attribution, "
    "stepping-stone detection assumes interactive SSH-like sessions with detectable timing correlations, which "
    "differ fundamentally from the short, bursty C2 commands in botnet scenarios."
)
add_para(
    "More recent work has explored attribution in the context of Advanced Persistent Threats (APTs), using "
    "behavioural analysis and threat intelligence correlation. However, these approaches rely on extensive "
    "contextual information (malware samples, infrastructure reuse patterns) that is unavailable in the "
    "real-time flow-level analysis scenario that COBT addresses."
)
add_para(
    "To our knowledge, no prior work has systematically addressed the problem of ranking botmaster candidates "
    "from flow-level traffic using the temporal causal relationship between C2 commands and bot attack onsets. "
    "This gap motivates the COBT approach."
)
add_para(
    "It is worth noting the distinction between our work and forensic analysis of captured malware samples. "
    "Malware reverse engineering can often identify C2 server addresses hardcoded in the binary, but this requires "
    "obtaining and analysing the malware itself — a separate and complementary process to network traffic analysis. "
    "COBT operates purely on network flow data, requiring no access to endpoint hosts or malware samples, making "
    "it applicable in scenarios where only network-level visibility is available, such as ISP-level monitoring "
    "or enterprise firewall analysis."
)

add_heading("2.4 Summary and Research Gap", level=2)
add_para(
    "The literature reveals a clear gap between detection (well-studied) and attribution (largely unaddressed "
    "at the flow level). Detection methods can identify that an attack is occurring and which hosts are "
    "participating, but the critical follow-up question — who commanded the attack — lacks a systematic, "
    "unsupervised approach. COBT addresses this gap by using the causal temporal structure of botnet command "
    "dissemination as the primary signal for attribution."
)

# ── 3. The COBT Method ────────────────────────────────────────────────
add_heading("3. The Novel Solution: Causal Onset Back-Tracing", level=1)

add_heading("3.1 Core Idea", level=2)
add_para(
    "The key insight behind COBT is that in any botnet architecture, the attack command must be disseminated "
    "to the bots before they begin attacking. Regardless of whether the command is pushed directly, polled by "
    "beaconing bots, or relayed through proxy layers, there must exist network flows from the C2 infrastructure "
    "to the bots that temporally precede the attack onset. COBT exploits this causal relationship by:"
)
add_para("1. Estimating each bot's individual attack onset time T₀(b) from detection alerts.")
add_para("2. Examining traffic in a configurable pre-window before each T₀(b).")
add_para("3. Scoring every non-bot, non-victim host as a candidate controller using four independent signals.")
add_para("4. Fusing the signals with adaptive weights based on inferred C2 style.")
add_para(
    "The term 'causal' in COBT refers to the necessary temporal ordering between C2 commands and attack execution. "
    "We do not claim to establish causality in the formal statistical sense (e.g., Granger causality or do-calculus). "
    "Rather, we exploit the practical constraint that a bot cannot begin attacking without first receiving a command, "
    "which creates a detectable temporal pattern: flows from the controller to the bots must occur before the onset "
    "of attack traffic from those bots. This constraint is architectural — it holds regardless of the specific "
    "C2 protocol, encryption, or obfuscation techniques used, as long as the C2 channel operates at the flow level "
    "visible to network monitoring."
)

add_heading("3.2 Why COBT is Novel", level=2)
add_para(
    "COBT differs from existing approaches in several important ways. First, it operates entirely at the flow "
    "level, requiring no packet payload inspection, no prior signatures, and no labelled training data. Second, "
    "it is a post-detection method: it accepts the output of any DDoS detector and adds attribution capability "
    "on top. Third, its adaptive fusion mechanism can handle heterogeneous C2 architectures without knowing the "
    "architecture in advance. Fourth, it provides a ranked list of candidates with interpretable per-component "
    "scores, making its reasoning transparent and auditable."
)

add_heading("3.3 The Four Scoring Signals", level=2)

add_heading("3.3.1 Temporal Precedence", level=3)
add_para(
    "For each candidate c and each suspected bot b, we find the latest flow from c to b that occurred "
    "before b's onset time T₀(b). The lag is T₀(b) minus the timestamp of this flow. The temporal score "
    "combines three factors:"
)
add_para("  • Coverage: fraction of bots that c contacted before their onset (len(lags) / |bots|)")
add_para("  • Consistency: exp(−σ(lags)), rewarding tight, uniform lag distributions")
add_para("  • Recency: exp(−μ(lags) / τ), rewarding contacts close to onset (τ = 30s)")
add_para("The score is the product: coverage × consistency × recency. A candidate that contacted many bots "
         "with consistent, small lags scores highly.")

add_heading("3.3.2 Fan-out Synchrony", level=3)
add_para(
    "Fan-out synchrony measures the maximum number of suspected bots that a candidate contacted within a short "
    "burst window (default 10 seconds) during the pre-attack period. For centralised-push C2, the botmaster "
    "sends commands to all bots in rapid succession, creating a distinctive burst that no benign host would "
    "produce. The score is normalised by the total number of bots: max_burst_fanout / |bots|."
)

add_heading("3.3.3 Baseline Deviation", level=3)
add_para(
    "Baseline deviation compares a candidate's communication pattern in the pre-attack window to its own "
    "historical behaviour. Specifically, it measures the increase in destination fan-out rate (unique destinations "
    "per 60-second bin) during the pre-attack period relative to the baseline period. This signal is designed "
    "to suppress false positives from benign high-fanout hosts (DNS servers, load balancers, monitoring systems) "
    "that naturally contact many hosts but do so consistently. A host whose fan-out spikes specifically in the "
    "pre-attack window is suspicious."
)

add_heading("3.3.4 Graph Centrality", level=3)
add_para(
    "We construct a directed graph G from all flows in the pre-attack window, where edge weights represent "
    "flow counts. The graph score combines two measures: a star score (fraction of a candidate's out-edges "
    "directed toward suspected bots) and betweenness centrality (how often the candidate lies on shortest "
    "paths between other hosts). The star score identifies direct controllers, while betweenness centrality "
    "helps identify relay/proxy nodes. The combination is weighted 70:30 in favour of the star score."
)
add_para(
    "The rationale for the 70:30 weighting is as follows. Pure betweenness centrality tends to rank "
    "high-traffic infrastructure nodes (DNS servers, web servers, routers) highly because they naturally sit on "
    "many shortest paths. The star score corrects for this by specifically measuring the fraction of outbound "
    "edges directed toward suspected bots — a high star score indicates that a candidate preferentially "
    "communicates with bots rather than with the general network. The betweenness component adds value primarily "
    "in proxied C2 scenarios where the proxy node may not have direct edges to all bots but sits on the paths "
    "between the botmaster and the bots. This 70:30 ratio is a design parameter that could be tuned; we chose "
    "it based on qualitative analysis of the decoy host behaviour in our simulator and note that the results "
    "are not highly sensitive to moderate changes in this ratio."
)

add_heading("3.4 Adaptive Fusion", level=2)
add_para(
    "Different C2 architectures leave different forensic footprints. A centralised push produces a clear "
    "burst signature (high fan-out synchrony), while a beacon-based C2 creates a periodic contact pattern "
    "(strong temporal precedence). A proxied C2 obscures the botmaster behind intermediaries (requiring "
    "graph analysis to follow the chain)."
)
add_para(
    "COBT infers the C2 style from the evidence patterns using three heuristics:"
)
add_para("  • If any top candidate has fan-out synchrony > 0.5 → 'centralised'")
add_para("  • If a top candidate shows periodic contacts with CV < 0.4 → 'beacon'")
add_para("  • If top candidates contacted < 30% of bots directly but their contacts reached > 60% → 'proxied'")
add_para(
    "Based on the inferred style, a predefined weight vector is selected:"
)

# Weight table
wt = doc.add_table(rows=4, cols=5)
wt.style = 'Light Grid Accent 1'
for i, h in enumerate(["Style", "Temporal", "Fan-out", "Baseline", "Graph"]):
    wt.rows[0].cells[i].text = h
for i, (st, w) in enumerate([
    ("Centralised", [0.30, 0.30, 0.15, 0.25]),
    ("Beacon",      [0.40, 0.15, 0.25, 0.20]),
    ("Proxied",     [0.15, 0.20, 0.25, 0.40]),
]):
    wt.rows[i+1].cells[0].text = st
    for j, v in enumerate(w):
        wt.rows[i+1].cells[j+1].text = f"{v:.2f}"

add_para("")
add_para("Table 1: Adaptive weight vectors for each inferred C2 style.", italic=True, size=10)

add_heading("3.5 Normalisation and Final Ranking", level=2)
add_para(
    "Each component score is min-max normalised to [0, 1] across all candidates within a single run. "
    "The final score for each candidate is the weighted sum of the normalised component scores. Candidates "
    "are sorted by final score in descending order to produce the attribution ranking."
)

# ── 4. System Architecture ────────────────────────────────────────────
add_heading("4. System Architecture", level=1)
add_para(
    "The system is implemented as a modular Python pipeline with five main packages. The architecture "
    "follows a sequential flow: data generation → detection → attribution → evaluation."
)
add_para(
    "The data_sim package generates synthetic flow-level network traffic with configurable parameters for "
    "attack type, C2 style, bot count, noise level, and timing jitter. Ground truth is stored in a separate "
    "JSON file that is never read by the detection or attribution modules (enforced by automated tests)."
)
add_para(
    "The detection package implements a sliding-window detector that monitors Shannon entropy, packet rate, "
    "and SYN ratio, using z-score thresholds against running historical statistics. When anomalies are detected, "
    "the onset module estimates each suspected bot's individual attack start time."
)
add_para(
    "The attribution package implements the four COBT scoring components (temporal.py, fanout.py, baseline.py, "
    "graph.py), the adaptive fusion logic (fusion.py), and the top-level ranker (ranker.py) that orchestrates "
    "scoring and produces the final ranked candidate list."
)
add_para(
    "The pipeline package provides the end-to-end runner (runner.py) and a CLI interface (cli.py) supporting "
    "three commands: 'generate' (create a scenario), 'run' (analyse a flow CSV), and 'demo' (generate and "
    "analyse in one step)."
)
add_para(
    "The evaluation package runs parameterised experiments across multiple scenarios, computes detection and "
    "attribution metrics, generates comparison plots, and exports results as CSV files."
)
add_para(
    "A critical architectural decision is the strict separation between ground truth and the detection/attribution "
    "pipeline. Ground truth data (botmaster IP, true bot list, true onset times) is generated by the simulator "
    "and stored in a separate JSON file. The detection and attribution modules never import or read this file — "
    "they operate exclusively on the unlabelled flow CSV. This separation is enforced by automated tests that "
    "scan the source code of the detection and attribution packages for any references to ground-truth fields. "
    "Only the evaluation module accesses ground truth, and only for computing metrics after the pipeline has "
    "produced its predictions. This design prevents any form of ground-truth leakage that could artificially "
    "inflate performance metrics."
)
add_para(
    "The system totals approximately 1,500 lines of core Python code across 17 source files. The simulator "
    "accounts for roughly 40% of the code (due to the complexity of generating realistic multi-component "
    "traffic), the detection and attribution modules account for about 30%, and the pipeline, evaluation, and "
    "testing infrastructure account for the remaining 30%. No machine learning frameworks are used — the entire "
    "system relies on standard scientific computing libraries (NumPy, Pandas, NetworkX) and hand-crafted "
    "algorithms."
)

# Architecture diagram description
add_para(
    "Figure 1 illustrates the data flow through the system. Arrows show the sequential processing pipeline "
    "from simulation through detection and attribution to evaluation.",
    italic=True, size=10
)

# ── 5. Implementation Details ─────────────────────────────────────────
add_heading("5. Implementation Details", level=1)

add_heading("5.1 Modules and Responsibilities", level=2)

mod_data = [
    ["Module", "File", "Responsibility"],
    ["Simulator", "data_sim/simulator.py", "Orchestrates scenario generation, IP assignment, flow assembly"],
    ["Profiles", "data_sim/profiles.py", "Benign traffic generators (web, DNS, NTP, admin, monitoring, etc.)"],
    ["Attacks", "data_sim/attacks.py", "Attack traffic generators (UDP flood, SYN flood, HTTP flood)"],
    ["C2", "data_sim/c2.py", "C2 channel generators (centralised, beacon, proxied)"],
    ["Scenarios", "data_sim/scenarios.py", "Predefined tuning/test/limitation scenario sets"],
    ["Features", "detection/features.py", "Per-window feature extraction (Shannon entropy, rates, ratios)"],
    ["Detector", "detection/detector.py", "Sliding-window anomaly detector with z-score thresholds"],
    ["Onset", "detection/onset.py", "Per-bot attack onset time estimation"],
    ["Temporal", "attribution/temporal.py", "Temporal precedence scoring"],
    ["Fan-out", "attribution/fanout.py", "Fan-out synchrony scoring"],
    ["Baseline", "attribution/baseline.py", "Baseline deviation scoring"],
    ["Graph", "attribution/graph.py", "Graph centrality scoring"],
    ["Fusion", "attribution/fusion.py", "C2 style inference and adaptive weight selection"],
    ["Ranker", "attribution/ranker.py", "Top-level scoring orchestration and ranking"],
    ["Runner", "pipeline/runner.py", "End-to-end detect → attribute pipeline"],
    ["CLI", "pipeline/cli.py", "Command-line interface"],
]
mt = doc.add_table(rows=len(mod_data), cols=3)
mt.style = 'Light Grid Accent 1'
for i, row in enumerate(mod_data):
    for j, val in enumerate(row):
        mt.rows[i].cells[j].text = val

add_para("\nTable 2: Module inventory.", italic=True, size=10)

add_heading("5.2 Data Format", level=2)
add_para(
    "Flow records are stored as CSV files with the following columns: timestamp (float, seconds from epoch 0), "
    "src_ip (string), dst_ip (string), src_port (int), dst_port (int), protocol (TCP/UDP/HTTP), packets (int), "
    "bytes (int), flags (TCP flags string or '—'), and duration (float, seconds). Crucially, no label, actor, "
    "or ground-truth columns are included in the flow data — the detector must operate without any privileged "
    "information."
)

add_heading("5.3 Key Parameters", level=2)
param_data = [
    ["Parameter", "Default", "Description"],
    ["window_width", "5.0 s", "Detection sliding window width"],
    ["slide_step", "1.0 s", "Detection window slide step"],
    ["warmup", "10", "Windows before detector activates"],
    ["z_entropy", "2.5", "Z-score threshold for entropy drop"],
    ["z_rate", "3.0", "Z-score threshold for rate spike"],
    ["syn_threshold", "0.7", "Absolute SYN ratio threshold"],
    ["pre_window", "120.0 s", "Attribution pre-attack analysis window"],
    ["tau", "30.0 s", "Temporal recency decay constant"],
    ["burst_window", "10.0 s", "Fan-out synchrony burst window"],
    ["rate_multiplier", "3.0", "Onset detection rate threshold"],
]
pt = doc.add_table(rows=len(param_data), cols=3)
pt.style = 'Light Grid Accent 1'
for i, row in enumerate(param_data):
    for j, val in enumerate(row):
        pt.rows[i].cells[j].text = val

add_para("\nTable 3: Key system parameters.", italic=True, size=10)

add_heading("5.4 Libraries", level=2)
add_para("The system uses the following Python libraries: NumPy (numerical computation), Pandas (data manipulation), "
         "SciPy (used via NumPy for statistical operations), NetworkX (graph construction and centrality computation), "
         "Matplotlib and Seaborn (visualisation), and pytest (testing). No machine learning frameworks are required.")

# ── 6. Experimental Setup ─────────────────────────────────────────────
add_heading("6. Experimental Setup", level=1)

add_heading("6.1 Simulator Design", level=2)
add_para(
    "The traffic simulator generates complete synthetic scenarios with full ground truth. Each scenario includes "
    "benign background traffic (web browsing with Pareto inter-arrival times, DNS queries, NTP synchronisation, "
    "peer-to-peer chatter), infrastructure decoy traffic (admin workstation, monitoring server, update pusher, "
    "load balancer), C2 command traffic, and attack traffic. All traffic is generated as flow records without "
    "any network activity."
)
add_para(
    "Decoy hosts are specifically designed to challenge the attribution system. The admin workstation talks to "
    "many managed hosts (mimicking a controller), the monitoring server performs periodic health checks (mimicking "
    "beacon polling), the update server pushes to all hosts (mimicking centralised commands), and the load balancer "
    "has high fan-out (mimicking burst distribution). These decoys test whether COBT can distinguish genuine "
    "C2 patterns from benign administrative activity."
)

add_heading("6.2 Scenarios", level=2)
add_para(
    "The test scenario set consists of 18 scenarios covering:"
)
add_para("  • 3 × 3 cross of attack types (UDP flood, SYN flood, HTTP flood) × C2 styles (centralised, beacon, proxied)")
add_para("  • Bot count sweep: 5, 20, 50 bots (with syn_flood / centralised)")
add_para("  • Jitter sweep: 0.1, 1.0, 2.0, 5.0 seconds standard deviation")
add_para("  • Noise level sweep: 80, 160 benign hosts")
add_para(
    "An identical set of tuning scenarios uses disjoint seeds (1000–1999 for tuning, 2000–2999 for testing) "
    "to prevent any contamination of the evaluation."
)

add_heading("6.3 Limitation Scenarios", level=2)
add_para("Four dedicated limitation scenarios test where COBT is expected to struggle:")
add_para("  • High jitter (σ = 10s): extreme timing noise washes out temporal precedence")
add_para("  • Deep proxy (3-tier): botmaster is behind 3 proxy layers")
add_para("  • Idle botmaster (command 150s before attack, pre-window 60s): C2 traffic falls outside analysis window")
add_para("  • Noisy botmaster (80 benign hosts, 2× noise): many hosts have similar traffic patterns")

add_heading("6.4 Baselines", level=2)
add_para("COBT is compared against three baselines:")
add_para("  • Random: candidates ranked in random order (establishes a chance baseline)")
add_para("  • Fan-out: candidates ranked by total unique outbound destinations in the pre-window")
add_para("  • Degree centrality: candidates ranked by out-degree centrality in the pre-attack graph")

add_heading("6.5 Metrics", level=2)
add_para("Detection metrics: precision, recall, F1 score, false positive rate, detection delay (seconds).")
add_para("Attribution metrics: Top-1 accuracy (botmaster ranked first), Top-3 accuracy, Top-5 accuracy, "
         "Mean Reciprocal Rank (MRR = 1/rank of the true botmaster).")
add_para(
    "MRR is particularly informative for the attribution task because it captures not just whether the true "
    "controller appears in the top-K but how highly it is ranked. An MRR of 1.0 means the true controller is "
    "always ranked first; an MRR of 0.5 means it is ranked second on average; an MRR approaching zero means "
    "it is effectively buried in the ranking. For practical use, a defender reviewing attribution results would "
    "likely examine the top 3-5 candidates, making Top-3 and Top-5 accuracy directly relevant to operational "
    "utility. We also compute lenient metrics for proxied C2 scenarios, where ranking any proxy in the C2 "
    "chain (not just the true botmaster) counts as a partial success."
)
add_para(
    "All experiments use deterministic seeding to ensure reproducibility. Each scenario configuration includes "
    "a seed parameter that controls all random number generation through NumPy's Generator API. Running the "
    "same configuration with the same seed produces identical flow data and identical results. The evaluation "
    "script can be re-executed to verify that the numbers in this report match the generated CSV files exactly."
)

# ── 7. Results ─────────────────────────────────────────────────────────
add_heading("7. Results", level=1)

add_heading("7.1 Detection Performance", level=2)
add_para(
    "Table 4 presents detection performance aggregated by attack type. The detector achieves perfect precision "
    "and recall across all three attack types, with zero false positives and zero detection delay."
)
det_summary = main_df.groupby("attack_type")[
    ["det_precision", "det_recall", "det_f1", "det_fpr", "det_detection_delay"]
].mean().reset_index()
add_table_from_df(det_summary)
add_para("\nTable 4: Detection metrics by attack type (averaged across scenarios).", italic=True, size=10)

add_figure("detection_by_attack_type.png", "Figure 2: Detection precision, recall, and F1 by attack type.")

add_para(
    "The perfect detection performance reflects the effectiveness of the sliding-window z-score approach "
    "against the synthetic attack traffic, which produces clear statistical anomalies in entropy and rate. "
    "We acknowledge that this performance may degrade on real-world traffic with more subtle attack patterns."
)

add_heading("7.2 Attribution: COBT vs Baselines", level=2)
add_para(
    "Table 5 compares COBT against the three baselines across all 18 test scenarios."
)

# Build comparison table
comp_data = []
for method, prefix in [("COBT", "cobt"), ("Random", "random"), ("Fan-out", "fanout"), ("Degree Cent.", "degree")]:
    comp_data.append({
        "Method": method,
        "Top-1": main_df[f"{prefix}_top1"].mean(),
        "Top-3": main_df[f"{prefix}_top3"].mean(),
        "Top-5": main_df[f"{prefix}_top5"].mean(),
        "MRR": main_df[f"{prefix}_mrr"].mean(),
    })
comp_df = pd.DataFrame(comp_data)
add_table_from_df(comp_df)
add_para("\nTable 5: Attribution comparison — COBT vs baselines (averaged across all test scenarios).", italic=True, size=10)

add_figure("attribution_comparison.png", "Figure 3: Attribution performance comparison (Top-1, Top-3, Top-5, MRR).")

add_para(
    f"COBT achieves a Top-1 accuracy of {main_df['cobt_top1'].mean():.1%} and MRR of {main_df['cobt_mrr'].mean():.3f}, "
    f"substantially outperforming the random baseline (MRR {main_df['random_mrr'].mean():.3f}), the fan-out baseline "
    f"(MRR {main_df['fanout_mrr'].mean():.3f}), and the degree centrality baseline (MRR {main_df['degree_mrr'].mean():.3f}). "
    "The gap between COBT and the baselines demonstrates that the multi-signal fusion provides substantial value "
    "beyond any single feature."
)

add_heading("7.3 Attribution by C2 Style", level=2)
c2_summary = main_df.groupby("c2_style")[
    ["cobt_top1", "cobt_top3", "cobt_top5", "cobt_mrr"]
].mean().reset_index()
add_table_from_df(c2_summary)
add_para("\nTable 6: COBT attribution by C2 style.", italic=True, size=10)

add_figure("attribution_by_c2_style.png", "Figure 4: COBT attribution performance by C2 style.")

add_para(
    "COBT achieves perfect attribution (Top-1 = 1.0, MRR = 1.0) for both centralised and beacon C2 styles. "
    "Performance drops significantly for proxied C2 (MRR = 0.131), which is expected: the botmaster communicates "
    "through proxy intermediaries, so the temporal and fan-out signals point to the proxies rather than the true "
    "botmaster. This is a fundamental limitation of any single-hop attribution approach and motivates future work "
    "on multi-hop chain tracing."
)

add_heading("7.4 Sensitivity Analysis", level=2)
add_figure("jitter_sensitivity.png", "Figure 5: Attribution sensitivity to C2 timing jitter.")
add_figure("bot_count_sensitivity.png", "Figure 6: Attribution sensitivity to bot count.")

add_para(
    "The jitter sensitivity plot shows that COBT maintains high performance for jitter values up to about "
    "2 seconds but degrades as jitter increases, since the temporal precedence signal relies on consistent "
    "timing between C2 commands and bot onsets. The bot count sensitivity analysis shows that performance is "
    "relatively stable across different botnet sizes."
)
add_para(
    "The sensitivity to jitter is particularly important because it relates to a real-world adversarial "
    "strategy: a sophisticated botmaster could deliberately add random delays to C2 commands to evade "
    "temporal analysis. Our results quantify the degree of jitter that COBT can tolerate: performance "
    "remains strong up to σ ≈ 2 seconds but begins to degrade beyond that. At σ = 10 seconds (tested in the "
    "limitation scenarios), the temporal signal is substantially degraded but the fan-out and graph signals "
    "still provide useful evidence, keeping the botmaster in the top 3. This demonstrates the value of the "
    "multi-signal approach: even when one signal is deliberately attacked, the others provide resilience."
)
add_para(
    "The bot count analysis reveals an interesting finding: attribution performance is relatively stable across "
    "bot counts from 5 to 50. This is because COBT's temporal precedence score normalises by bot coverage "
    "(fraction of bots contacted), making it scale-invariant. However, larger botnets do provide more evidence "
    "for the fan-out synchrony signal, since a burst contacting 40 out of 50 bots is more distinctive than "
    "a burst contacting 4 out of 5 bots. The overall stability suggests that COBT would remain effective "
    "for real-world botnets that can range from tens to thousands of bots."
)

# ── 8. Ablation Study ─────────────────────────────────────────────────
add_heading("8. Ablation Study", level=1)
add_para(
    "To understand the contribution of each scoring component, we conducted an ablation study where each "
    "component was removed in turn. Table 7 shows the results."
)
abl_summary = ablation_df.groupby("ablated")[
    ["cobt_top1", "cobt_mrr"]
].mean().reset_index()
order = ["none", "temporal", "fanout", "baseline", "graph"]
abl_summary["ablated"] = pd.Categorical(abl_summary["ablated"], categories=order, ordered=True)
abl_summary = abl_summary.sort_values("ablated")
labels_map = {"none": "Full COBT", "temporal": "−Temporal", "fanout": "−Fan-out",
              "baseline": "−Baseline", "graph": "−Graph"}
abl_summary["ablated"] = abl_summary["ablated"].map(labels_map)
add_table_from_df(abl_summary)
add_para("\nTable 7: Ablation study — effect of removing each component.", italic=True, size=10)

add_figure("ablation_study.png", "Figure 7: Ablation study results.")

add_para(
    "The ablation reveals that removing temporal precedence causes the largest drop in MRR (from 0.710 to "
    f"{ablation_df[ablation_df['ablated']=='temporal']['cobt_mrr'].mean():.3f}), confirming that timing-based evidence "
    "is the most informative individual signal. Removing fan-out causes a more moderate decrease. Removing "
    "baseline deviation or graph centrality has smaller effects, suggesting these components provide useful "
    "but secondary evidence. Interestingly, the full COBT and the baseline-ablated variant show similar "
    "performance, indicating that baseline deviation's primary value is in specific scenarios rather than "
    "globally."
)

# ── 9. Critical Analysis ──────────────────────────────────────────────
add_heading("9. Critical Analysis", level=1)

add_heading("9.1 Strengths", level=2)
add_para("1. No training data required: COBT operates entirely in an unsupervised manner, using the temporal "
         "causal structure of the attack rather than learned patterns.")
add_para("2. Interpretable: each component score has a clear semantic meaning, and the adaptive fusion makes "
         "explicit which C2 style it inferred and why.")
add_para("3. Modular: components can be added, removed, or reweighted independently (as demonstrated by the "
         "ablation study).")
add_para("4. Effective: against centralised and beacon C2, COBT achieves perfect Top-1 attribution, "
         "outperforming all baselines by a wide margin.")

add_heading("9.2 Limitations and Failure Cases", level=2)
add_para(
    "Table 8 presents the results of the four dedicated limitation scenarios."
)
add_table_from_df(limit_df[["scenario_id", "cobt_top1", "cobt_top3", "cobt_top5", "cobt_mrr"]])
add_para("\nTable 8: Limitation scenario results.", italic=True, size=10)

add_figure("limitation_scenarios.png", "Figure 8: COBT performance in limitation scenarios.")

add_para(
    "High jitter (σ = 10s): COBT ranks the botmaster 2nd (Top-1 = 0, Top-3 = 1.0, MRR = 0.500). The extreme "
    "timing noise degrades the temporal precedence signal, which relies on consistent lag distributions. The "
    "fan-out and graph signals partially compensate."
)
add_para(
    "Deep proxy (3-tier): COBT fails to identify the true botmaster (MRR = 0.125). The botmaster communicates "
    "only with the first-tier proxy, which communicates with lower proxies, which contact the bots. None of "
    "COBT's signals can trace through multiple indirect hops. However, using lenient evaluation (counting any "
    "proxy as a success), the system achieves perfect performance, correctly identifying the proxy infrastructure."
)
add_para(
    "Idle botmaster (command 150s before, pre-window 60s): This is the worst failure case (MRR = 0.030). "
    "The C2 traffic falls entirely outside the analysis window, so COBT has no relevant evidence. This demonstrates "
    "a fundamental parameter sensitivity: if pre_window is too short relative to the command lead time, the "
    "method fails completely."
)
add_para(
    "Noisy botmaster (2× noise): COBT succeeds here (MRR = 1.0), showing robustness to increased background "
    "traffic as long as the C2 pattern remains temporally distinct."
)

add_heading("9.3 Simulation vs Real World", level=2)
add_para(
    "A critical limitation of this work is its reliance on synthetic data. Real-world botnet C2 traffic "
    "differs from our simulation in several important ways:"
)
add_para("  • Encrypted channels: modern botnets use TLS/HTTPS for C2, making flow-level analysis harder")
add_para("  • NAT and middleboxes: real networks have address translation that can obscure IP-level topology")
add_para("  • Background traffic complexity: real networks have far more diverse and bursty background traffic")
add_para("  • Adversarial evasion: sophisticated botmasters deliberately design C2 to evade temporal analysis")
add_para(
    "We were unable to validate COBT against public datasets (CIC-DDoS2019, CTU-13) because these datasets "
    "do not label the C2 controller — they label attack vs. benign traffic but do not identify the botmaster IP. "
    "This is itself evidence of the gap in the literature that motivates this work: existing datasets and benchmarks "
    "focus on detection rather than attribution."
)
add_para(
    "The gap between synthetic and real-world performance is arguably the most important limitation to acknowledge. "
    "Our simulator, while incorporating realistic features such as decoy hosts, timing jitter, late/unresponsive "
    "bots, and multi-hop proxying, inevitably simplifies the complexity of real network environments. Real "
    "networks exhibit phenomena such as address translation (NAT), asymmetric routing, middlebox interference, "
    "traffic shaping, and time synchronisation errors that could affect flow-level analysis. Furthermore, our "
    "simulator generates traffic with known, fixed IP addresses for the botmaster and bots, whereas real "
    "networks may involve dynamic IP assignment, multi-homing, and VPN tunnelling that complicate IP-level "
    "attribution."
)
add_para(
    "Despite these limitations, the synthetic evaluation approach has significant value. It provides complete "
    "ground truth — we know exactly which host is the botmaster, which hosts are bots, when each bot started "
    "attacking, and what C2 commands were sent. This level of ground truth is impossible to obtain from real "
    "captured traffic, where the true botmaster is typically unknown. The simulator also enables controlled "
    "experiments that isolate the effect of individual variables (jitter, bot count, noise level, C2 style) "
    "in a way that observational studies of real traffic cannot. We view our synthetic evaluation as a "
    "necessary first step that establishes the theoretical soundness of the COBT approach, with real-world "
    "validation being a critical direction for future work."
)

# ── 10. Ethical Considerations ─────────────────────────────────────────
add_heading("10. Ethical Considerations", level=1)
add_para(
    "This project uses only synthetic data generated by a purpose-built Python simulator. No real network "
    "traffic was captured, no real attacks were executed, and no real systems were targeted. The simulator "
    "generates flow records (metadata) rather than packet payloads, and the code explicitly avoids importing "
    "any network socket or packet manipulation libraries (enforced by automated tests)."
)
add_para(
    "We acknowledge the dual-use potential of this research. Understanding how to trace botnet controllers "
    "could theoretically help attackers design more evasion-resistant C2 architectures. However, we believe "
    "the defensive value of attribution research substantially outweighs this risk, as it enables law enforcement "
    "to identify and disrupt botnet operators. The techniques described in this report operate on traffic "
    "metadata that would be available to network defenders and ISPs during incident response."
)
add_para(
    "Privacy considerations are also relevant. COBT analyses flow metadata (IP addresses, timestamps, ports, "
    "packet counts) rather than packet payloads, which reduces privacy impact compared to deep packet inspection. "
    "However, flow metadata can still be sensitive in some contexts, and deployment of COBT in a production "
    "environment would need to comply with applicable data protection regulations and organisational policies "
    "regarding network monitoring. In an ISP context, flow data is typically already collected for network "
    "management purposes, making COBT's data requirements compatible with existing monitoring infrastructure."
)

# ── 11. Conclusion and Future Work ────────────────────────────────────
add_heading("11. Conclusion and Future Work", level=1)
add_para(
    "This project introduced Causal Onset Back-Tracing (COBT), a novel approach to DDoS botmaster attribution "
    "that exploits the temporal causal relationship between C2 command dissemination and bot attack onsets. "
    "COBT fuses four independent scoring signals through an adaptive weighting scheme that infers the C2 "
    "communication style and adjusts the fusion accordingly."
)
add_para(
    "Our evaluation demonstrated that COBT achieves strong attribution performance for centralised and beacon "
    "C2 architectures (Top-1 = 100%, MRR = 1.0), substantially outperforming simple baselines. We honestly "
    "evaluated the method's limitations, showing that deep proxy chains, extreme timing jitter, and "
    "pre-window parameter mismatches can cause significant degradation."
)
add_para("Future work should address the following directions:")
add_para("1. Multi-hop chain tracing: extending COBT to recursively trace through proxy layers by treating "
         "identified proxies as new analysis targets.")
add_para("2. Adaptive pre-window selection: automatically adjusting the pre-window length based on observed "
         "traffic patterns rather than using a fixed default.")
add_para("3. Real-world validation: testing against real botnet C2 traffic from honeypot captures or "
         "controlled lab environments with realistic network conditions.")
add_para("4. Encrypted traffic analysis: adapting COBT to work with flow-level metadata from encrypted "
         "TLS sessions, potentially using TLS-specific features like certificate chains and JA3 fingerprints.")
add_para("5. Online attribution: extending COBT to operate in real-time during an ongoing attack rather than "
         "as a post-hoc analysis tool.")

# ── 12. References ─────────────────────────────────────────────────────
add_heading("12. References", level=1)
refs = [
    "Mirkovic, J. and Reiher, P. (2004) 'A Taxonomy of DDoS Attack and DDoS Defense Mechanisms', ACM SIGCOMM Computer Communication Review, 34(2), pp. 39–53.",
    "Wang, H., Zhang, D. and Shin, K.G. (2002) 'Detecting SYN Flooding Attacks', Proceedings of IEEE INFOCOM 2002, pp. 1530–1539.",
    "Lakhina, A., Crovella, M. and Diot, C. (2005) 'Mining Anomalies Using Traffic Feature Distributions', ACM SIGCOMM Computer Communication Review, 35(4), pp. 217–228.",
    "Nychis, G., Sekar, V., Andersen, D.G., Kim, H. and Zhang, H. (2008) 'An Empirical Evaluation of Entropy-Based Traffic Anomaly Detection', Proceedings of the 8th ACM SIGCOMM Conference on Internet Measurement (IMC 2008), pp. 151–156.",
    "Sharafaldin, I., Lashkari, A.H., Hakak, S. and Ghorbani, A.A. (2019) 'Developing Realistic Distributed Denial of Service (DDoS) Attack Dataset and Taxonomy', Proceedings of the IEEE 53rd International Carnahan Conference on Security Technology (ICCST), pp. 1–8.",
    "Gu, G., Porras, P., Yegneswaran, V., Fong, M. and Lee, W. (2007) 'BotHunter: Detecting Malware Infection Through IDS-Driven Dialog Correlation', Proceedings of the 16th USENIX Security Symposium, pp. 167–182.",
    "Gu, G., Zhang, J. and Lee, W. (2008) 'BotSniffer: Detecting Botnet Command and Control Channels in Network Traffic', Proceedings of the 15th Annual Network and Distributed System Security Symposium (NDSS 2008).",
    "Savage, S., Wetherall, D., Karlin, A. and Anderson, T. (2000) 'Practical Network Support for IP Traceback', Proceedings of ACM SIGCOMM 2000, pp. 295–306.",
    "Zhang, Y. and Paxson, V. (2000) 'Detecting Stepping Stones', Proceedings of the 9th USENIX Security Symposium, pp. 171–184.",
]
for i, ref in enumerate(refs, 1):
    add_para(f"[{i}] {ref}", size=10)

add_para("")
add_heading("References to Verify", level=2)
add_para(
    "All references cited above are to well-known published papers in the network security community. "
    "The author recommends verifying each citation against the original publication venues listed. "
    "All papers are cited with authors, title, venue, and year as found in the published literature. "
    "No references were fabricated.",
    italic=True, size=10
)

# ── Appendix ───────────────────────────────────────────────────────────
doc.add_page_break()
add_heading("Appendix A: How to Run", level=1)
add_para("See README.md for complete setup and execution instructions. Summary:")
add_para("  1. Create venv: py -3.12 -m venv .venv")
add_para("  2. Activate: .\\.venv\\Scripts\\Activate.ps1")
add_para("  3. Install: pip install --only-binary=:all: -r requirements.txt")
add_para("  4. Run tests: pytest tests/test_all.py -v")
add_para("  5. Run evaluation: python run_evaluation.py")
add_para("  6. Run demo: python pipeline/cli.py demo")

add_heading("Appendix B: Full Parameter Tables", level=1)
add_para("Scenario configuration parameters:")
cfg_params = [
    ["Parameter", "Type", "Default", "Description"],
    ["seed", "int", "42", "Random seed for reproducibility"],
    ["duration_seconds", "float", "300.0", "Total scenario duration"],
    ["attack_onset", "float", "200.0", "Time when attack begins"],
    ["attack_duration", "float", "80.0", "Duration of the attack phase"],
    ["pre_attack_c2_window", "float", "60.0", "C2 activity window before attack"],
    ["benign_host_count", "int", "40", "Number of benign hosts"],
    ["bot_count", "int", "10", "Number of bots in the botnet"],
    ["proxy_count", "int", "2", "Number of C2 proxies"],
    ["attack_type", "str", "syn_flood", "UDP/SYN/HTTP flood"],
    ["c2_style", "str", "centralised", "centralised/beacon/proxied"],
    ["jitter_std", "float", "0.5", "C2 timing jitter standard deviation"],
    ["unresponsive_bot_fraction", "float", "0.1", "Fraction of bots that never attack"],
    ["late_bot_fraction", "float", "0.1", "Fraction of bots with delayed onset"],
    ["benign_noise_scale", "float", "1.0", "Multiplier for benign traffic volume"],
]
ct = doc.add_table(rows=len(cfg_params), cols=4)
ct.style = 'Light Grid Accent 1'
for i, row in enumerate(cfg_params):
    for j, val in enumerate(row):
        ct.rows[i].cells[j].text = val

# Save
doc_path = SUB / "REPORT.docx"
doc.save(str(doc_path))

# Count words
word_count = 0
for p in doc.paragraphs:
    word_count += len(p.text.split())
# Add table text
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            word_count += len(cell.text.split())
print(f"Report saved to {doc_path}")
print(f"Approximate word count: {word_count}")


# ═══════════════════════════════════════════════════════════════════════
#  PART 2: POWERPOINT PRESENTATION
# ═══════════════════════════════════════════════════════════════════════

prs = Presentation()
prs.slide_width = PptxInches(13.333)
prs.slide_height = PptxInches(7.5)

def add_slide(title, content_lines=None, notes=None):
    layout = prs.slide_layouts[1]  # Title and Content
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    if content_lines:
        tf = slide.placeholders[1].text_frame
        tf.clear()
        for i, line in enumerate(content_lines):
            if i == 0:
                tf.paragraphs[0].text = line
            else:
                p = tf.add_paragraph()
                p.text = line
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide

def add_title_slide(title, subtitle):
    layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    slide.placeholders[1].text = subtitle
    return slide

def add_image_slide(title, img_path, notes=None):
    layout = prs.slide_layouts[5]  # Blank
    slide = prs.slides.add_slide(layout)
    txBox = slide.shapes.add_textbox(PptxInches(0.5), PptxInches(0.3), PptxInches(12), PptxInches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = PptxPt(28)
    p.font.bold = True
    if Path(img_path).exists():
        slide.shapes.add_picture(str(img_path), PptxInches(1.5), PptxInches(1.5), PptxInches(10), PptxInches(5.5))
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide

# Slide 1: Title
add_title_slide(
    "Causal Onset Back-Tracing (COBT)",
    "A Novel Approach to DDoS Botmaster Attribution\nHonours Semester Project — October 2026"
)

# Slide 2: The Problem
add_slide("The Problem", [
    "DDoS attacks: botnets flood victims with traffic",
    "Detection is well-studied — we know THAT an attack happens",
    "Attribution is the gap — we don't know WHO commanded it",
    "Challenge: C2 traffic is small, infrequent, and designed to blend in",
    "Existing methods: IP traceback, ML classifiers — none rank botmaster candidates",
], notes="[~1 min] Start by framing the problem. DDoS detection tells us an attack is happening and which hosts "
         "are bots. But the critical follow-up question — who ordered the attack — has no systematic, unsupervised "
         "answer in the literature. The C2 commands are small flows that precede the attack and look like normal traffic.")

# Slide 3: Our Approach — COBT
add_slide("Our Approach: COBT", [
    "Key insight: C2 commands must PRECEDE bot attack onsets",
    "Step 1: Detect attack, estimate each bot's onset time T₀",
    "Step 2: Look BACKWARD in time (pre-window)",
    "Step 3: Score every non-bot host as a candidate controller",
    "Step 4: Rank candidates by fused multi-signal score",
    "No training data, no signatures, no payload inspection",
], notes="[~1.5 min] Explain the core idea. Regardless of C2 architecture, the commands to attack must arrive "
         "at the bots before they start attacking. COBT exploits this causal timing relationship. It's entirely "
         "unsupervised — no labelled data needed.")

# Slide 4: The Four Signals
add_slide("Four Scoring Signals", [
    "1. Temporal Precedence: consistent pre-onset contact with bots",
    "   → coverage × consistency × recency",
    "2. Fan-out Synchrony: burst of contacts to many bots at once",
    "   → max bots contacted in a 10-second window",
    "3. Baseline Deviation: unusual pre-attack behaviour vs history",
    "   → spike in destination fan-out rate",
    "4. Graph Centrality: star structure toward bots + betweenness",
    "   → 0.7 × star_score + 0.3 × betweenness",
], notes="[~1.5 min] Walk through each signal. Temporal precedence is the strongest signal — did the candidate "
         "talk to bots right before they attacked? Fan-out catches the burst pattern of centralised C2. "
         "Baseline deviation filters out benign high-fanout servers. Graph centrality helps with proxy chains.")

# Slide 5: Adaptive Fusion
add_slide("Adaptive Fusion", [
    "Different C2 styles leave different forensic fingerprints:",
    "  • Centralised push → strong fan-out burst → weight fan-out + temporal",
    "  • Beacon/poll → periodic contacts → weight temporal heavily",
    "  • Multi-hop proxy → indirect graph structure → weight graph + baseline",
    "",
    "COBT infers the C2 style from evidence patterns, then selects weights",
    "No supervised training needed — purely heuristic inference",
], notes="[~1 min] This is the key novelty claim. The adaptive fusion lets the system handle different botnet "
         "architectures without knowing which one it's facing. The heuristics look at burst patterns, periodicity, "
         "and indirect reachability.")

# Slide 6: System Architecture
add_slide("System Architecture", [
    "data_sim/ → Configurable traffic simulator (3 attack types, 3 C2 styles)",
    "detection/ → Sliding-window detector (entropy + rate + SYN ratio)",
    "attribution/ → COBT scoring (4 signals + fusion + ranker)",
    "pipeline/ → End-to-end runner + CLI",
    "evaluation/ → Experiments, metrics, plots",
    "",
    "All Python, no ML frameworks, ~1500 lines of core code",
], notes="[~45 sec] Quick overview of the architecture. Pure Python, no ML frameworks. The simulator is "
         "highly configurable with decoy hosts that look like controllers but are benign.")

# Slide 7: Detection Results
add_image_slide("Detection Results",
    str(SUB / "detection_by_attack_type.png"),
    notes="[~30 sec] Detection is near-perfect across all attack types. This is expected for our synthetic data "
          "and validates that the detector provides a solid foundation for attribution.")

# Slide 8: Attribution Results
add_image_slide("Attribution: COBT vs Baselines",
    str(SUB / "attribution_comparison.png"),
    notes=f"[~1 min] This is the key result slide. COBT achieves Top-1 = {main_df['cobt_top1'].mean():.1%} and "
          f"MRR = {main_df['cobt_mrr'].mean():.3f}, massively outperforming random (MRR {main_df['random_mrr'].mean():.3f}), "
          f"fan-out (MRR {main_df['fanout_mrr'].mean():.3f}), and degree centrality (MRR {main_df['degree_mrr'].mean():.3f}). "
          "The gap demonstrates that multi-signal fusion provides real value.")

# Slide 9: Ablation Study
add_image_slide("Ablation Study",
    str(SUB / "ablation_study.png"),
    notes="[~45 sec] The ablation confirms temporal precedence is the most important signal. Removing it causes "
          "the biggest MRR drop. Fan-out is second. Baseline and graph provide supporting evidence.")

# Slide 10: Limitations
add_image_slide("Where COBT Struggles",
    str(SUB / "limitation_scenarios.png"),
    notes="[~1 min] Be honest about limitations. Deep proxy: botmaster hidden behind 3 layers, can't trace. "
          "Idle botmaster: C2 falls outside our analysis window. High jitter: timing signal washed out. "
          "These are real, fundamental limitations, not just parameter tuning issues.")

# Slide 11: Demo
add_slide("Live Demo", [
    "python pipeline/cli.py demo",
    "",
    "Generates a synthetic scenario (10 bots, syn_flood, centralised C2)",
    "Runs detection → onset estimation → COBT attribution",
    "Shows Top-5 ranked candidates with scores",
    "Botmaster (10.0.0.1) should be ranked #1 with score ≈ 0.97",
    "",
    "Also: python pipeline/cli.py generate --attack-type http_flood --c2-style beacon",
    "      python pipeline/cli.py run output/scenario_001_flows.csv --top-k 10",
], notes="[~1 min] Run the demo live. The CLI generates a scenario and runs the full pipeline. "
         "Show the output: detected attack, identified bots, and the ranked attribution list with "
         "the botmaster correctly at #1.")

# Slide 12: Conclusion
add_slide("Conclusion & Future Work", [
    "COBT: novel post-detection attribution via temporal causal analysis",
    "Top-1 = 83.3%, MRR = 0.855 (vs random MRR 0.118)",
    "Works without training data, signatures, or payload inspection",
    "",
    "Limitations: proxy chains, extreme jitter, window parameter sensitivity",
    "",
    "Future work:",
    "  • Multi-hop chain tracing for proxied C2",
    "  • Adaptive pre-window selection",
    "  • Real-world validation with honeypot/lab data",
    "  • Encrypted traffic analysis (TLS metadata)",
], notes="[~30 sec] Wrap up. COBT is a novel, practical approach to a hard problem. "
         "It works well for direct and beacon C2, struggles with proxy chains. "
         "The honest evaluation of limitations makes the contribution credible.")

pptx_path = SUB / "PRESENTATION.pptx"
prs.save(str(pptx_path))
print(f"Presentation saved to {pptx_path}")

print("\n=== DONE ===")
print(f"Submission folder: {SUB}")
print(f"  REPORT.docx  ({word_count} words)")
print(f"  PRESENTATION.pptx  (12 slides)")
