# DRTS Mini-Project 2 — TSN Analysis & Simulation
**02225 Distributed Real-Time Systems | Technical University of Denmark (DTU)**

---

## Overview

This project provides a suite of tools for evaluating and visualizing Time-Sensitive Networking (TSN) experiments. It focuses on comparing two traffic scheduling mechanisms: **Strict Priority (SP)** and **Credit-Based Shaper (CBS)**.

The suite includes four primary tools: an analytical Worst-Case Response Time (WCRT) calculator, a discrete-event simulator, a network topology visualizer, and a timeline/Gantt chart generator. All tools are designed to read modular network configurations from structured JSON test cases.

## Project Structure

```text
DRTS-Mini-Project-2/
│
├── analysis.py             # Compositional WCRT calculator
├── simulation.py           # Discrete-event network simulator
├── visualize.py            # Network topology and queue visualizer
├── timeline_visualize.py   # SP vs CBS Gantt chart concept visualizer
├── README.md               # This file
│
└── TestCases/              # Subfolders containing JSON network configurations
    ├── test_case_1/
    ├── test_case_2/
    ├── test_case_starvation/
    ├── test_case_starve/
    └── ...
```

## Requirements

Make sure you have **Python 3** installed along with the following library:

```bash
pip install matplotlib networkx numpy
```

## Input Data Format

All tools (except the timeline visualizer) dynamically load their configuration from a specified folder inside the `TestCases/` directory. A valid test case folder must contain:

- `topology.json` — Defines nodes, links, and bandwidth.
- `streams.json` — Defines traffic flows (ID, PCP priority, size, period).
- `routes.json` — Maps flows to specific network paths.
- `config.json` (Optional) — Defines CBS slopes (idle/send rates). Defaults to `0.5` if missing.

## How to Run

Navigate to the `DRTS-Mini-Project-2/` directory in your terminal. You can run the tools using the `--TestCase` flag to point to any folder inside `TestCases/`.

### 1. Analytical Tool (`analysis.py`)

Computes the theoretical Worst-Case Response Time (WCRT) for each stream using compositional analysis across all links in the route.

```bash
python analysis.py --TestCase <folder_name>
```

**Example:**

```bash
python analysis.py --TestCase test_case_starve
```

Outputs a formatted table comparing SP WCRT and CBS WCRT (in microseconds).

### 2. Simulation Tool (`simulation.py`)

Runs a discrete-event simulation tracking packet generation, queueing, and exact transmission times over the network hyperperiod.

```bash
python simulation.py --TestCase <folder_name>
```

**Example:**

```bash
python simulation.py --TestCase test_case_starvation
```

Outputs the empirically observed Maximum Delay per stream, or `STARVED` if a lower-priority stream is completely blocked by SP.

### 3. Network Visualizer (`visualize.py`)

Generates an interactive 2D graph of the network topology, explicitly showing which egress queues (PCP 0, 1, 2) are active on each link.

```bash
python visualize.py --TestCase <folder_name>
```

**Example:**

```bash
python visualize.py --TestCase test_case_2
```

### 4. Timeline Visualizer (`timeline_visualize.py`)

A standalone conceptual visualization tool that generates a Gantt chart comparing how SP and CBS allocate bandwidth over time, highlighting the "starvation" phenomenon.

```bash
python timeline_visualize.py
```

## Troubleshooting

- **FileNotFoundError:** Ensure the folder name you pass to `--TestCase` exactly matches a folder inside the `TestCases/` directory, and that it contains the required JSON files.
- **Empty Output / Exits Early:** Verify that the `streams.json` file has valid `period` and `size` values, and that `routes.json` correctly maps flow IDs to valid topology nodes.
- **Decimal Formatting:** Output tables use European comma formatting (e.g., `400,0`) to align with standard reporting requirements.

---

*Group 37 — Afonso Martim Domingues, Jeppe Weikop, Jonas Høyer, Tor Carlos Høydahl Ohme, William Allerup Carlsen*
