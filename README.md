# DDoS Causal Onset Back-Tracing (COBT)

**About This Project**
I built this project to help an Honours student with their university project. It is designed to solve a major problem in cybersecurity: when a website is hit by a massive cyberattack (called a DDoS attack), it is very hard to figure out who actually ordered the attack. 

**What is a DDoS attack?** 
Imagine thousands of people trying to enter a small store at exactly the same time. The store gets overwhelmed and nobody can buy anything. A DDoS (Distributed Denial of Service) attack is similar: a hacker (the "botmaster") secretly takes control of thousands of normal computers around the world. When the hacker gives the command, all those computers flood a target website with junk traffic, causing the website to crash.

**What does this code do?**
Most security tools only focus on stopping the junk traffic. This project goes a step further: it acts like a digital detective. 
1. **The Simulator** creates a fake network with normal traffic, a fake hacker, and fake compromised computers.
2. **The Detector** watches the traffic and spots exactly when the attack starts.
3. **The Attributor (COBT)** is the brain of the project. It looks backward in time right before the attack started to find the hidden "Go!" commands sent by the hacker. By analyzing timing and connection patterns, it creates a "most wanted" list, ranking the most likely computers that belong to the hacker.

This code proves that by using clever math and timing analysis, we can trace a cyberattack back to its source without needing to look inside the encrypted data packets.

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
