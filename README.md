# DDoS Causal Onset Back-Tracing (COBT)

**Context & Background**
I developed this project to help an Honours student with their semester project on network security and DDoS attribution. The goal was to provide a rigorous, from-scratch implementation of a novel post-detection attribution algorithm called Causal Onset Back-Tracing (COBT). The project involved creating a synthetic evaluation testbed, detection pipeline, and the core attribution system to demonstrate how one might trace a DDoS attack back to the original botmaster without relying on packet payloads or supervised machine learning.

## What Everything Does

This repository contains a complete synthetic pipeline to evaluate the COBT algorithm. Here is a breakdown of the components:

- `data_sim/`: The network traffic simulator. This module generates flow-level traffic data including benign background noise (web, DNS, NTP), infrastructure decoys (admin workstations, load balancers), C2 command traffic (centralised, beacon, proxied), and the actual attack traffic (UDP, SYN, HTTP floods). It outputs a CSV of flows and a separate JSON file containing ground-truth labels.
- `detection/`: The sliding-window anomaly detector. It processes the unlabelled flow CSV, tracking Shannon entropy and packet rates. When statistical anomalies occur (e.g., entropy drops as traffic converges on a victim), it flags an alert and uses a micro-window approach to estimate the precise attack onset time for each suspected bot.
- `attribution/`: The core COBT logic. This module looks backward in time from each bot's estimated onset to find the causal command flows. It scores candidates based on four signals:
  - `temporal.py`: Measures how consistently a candidate contacts bots just before they attack.
  - `fanout.py`: Detects sudden bursts of contacts to multiple bots (indicative of centralised C2).
  - `baseline.py`: Checks if a candidate's fan-out rate spiked unusually compared to its historical behavior.
  - `graph.py`: Builds a pre-attack interaction graph and scores candidates based on star-topology centrality and betweenness.
  - `fusion.py`: Adaptively infers the C2 style and weights the four signals to produce a final attribution score.
  - `ranker.py`: Orchestrates the scoring and returns a ranked list of botmaster candidates.
- `pipeline/`: Connects the simulator, detector, and attributor. It includes `runner.py` for programmatic execution and `cli.py` for command-line interactions (generate, run, demo).
- `evaluation/`: Orchestrates large-scale experiments across multiple scenarios (different attacks, C2 styles, bot counts, noise levels). It computes metrics (Precision, Recall, F1, MRR) and generates performance plots and CSV reports.
- `tests/`: A comprehensive `pytest` suite that verifies system functionality and strictly ensures there is no "ground truth leakage" (the detector and attributor cannot access the secret labels).
- `run_evaluation.py`: The main entry point to execute the full evaluation suite and generate the contents of the `report/` directory.
- `generate_submission.py`: A utility script that compiles the experimental results into a comprehensive Word document report and a PowerPoint presentation.

## Requirements

- Python 3.11 or 3.12 (Python 3.14+ is not fully supported by some dependencies yet)
- OS: Windows, Linux, or macOS

## Setup Instructions

1. **Create a virtual environment:**
   ```bash
   # Windows
   py -3.12 -m venv .venv
   
   # Linux/macOS
   python3.12 -m venv .venv
   ```

2. **Activate the virtual environment:**
   ```bash
   # Windows (Command Prompt)
   .venv\Scripts\activate.bat
   
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source .venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install --only-binary=:all: -r requirements.txt
   ```

## Running the Evaluation

To execute the entire pipeline (simulator -> detector -> attributor), run the evaluation script from the root of the project:

```bash
python run_evaluation.py
```

This runs multiple scenarios (different attack types, C2 structures, noise levels) and generates performance tables in the console. It outputs a `report/` directory containing CSV metrics and visualization plots.

## Running the Tests

To verify the integrity of the project and ensure there is no ground truth leakage, run:

```bash
pytest tests/test_all.py -v
```
