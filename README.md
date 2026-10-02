# DDoS Causal Onset Back-Tracing (COBT)

This project provides a complete synthetic pipeline to evaluate Causal Onset Back-Tracing (COBT), a novel algorithm for identifying botmasters and command-and-control (C2) servers in a DDoS attack. It includes a highly configurable traffic simulator, a sliding-window detector to flag suspected bots via onset anomalies, and an attribution component that fuses temporal precedence, fan-out synchrony, baseline deviations, and graph centrality to rank likely controllers. The full end-to-end evaluation validates the COBT method against multiple attack types, C2 styles, and network conditions.

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

## Project Structure

- `data_sim/`: The network traffic simulator that generates flows and ground-truth labels.
- `detection/`: The sliding-window algorithm that detects DDoS onsets and identifies suspected bots.
- `attribution/`: The COBT components (`temporal.py`, `fanout.py`, `baseline.py`, `graph.py`, `fusion.py`) for ranking controllers.
- `pipeline/`: High-level runners and evaluation frameworks linking everything together.
- `tests/`: Unit and integration test suites validating end-to-end functionality and ensuring no ground-truth leakage.
- `run_evaluation.py`: The entry point for executing the experimental testbed and generating results.

## Running the Evaluation

To execute the entire pipeline (simulator -> detector -> attributor), run the evaluation script from the root of the project:

```bash
python run_evaluation.py
```

This will run multiple scenarios (different attack types, C2 structures, noise levels) and generate performance tables in the console. It will also output a `report/` directory containing CSV metrics and visualization plots (e.g., Precision-Recall curves, ablation charts).

## Running the Tests

To verify the integrity of the project and ensure there is no ground truth leakage, run:

```bash
pytest tests/test_all.py -v
```
