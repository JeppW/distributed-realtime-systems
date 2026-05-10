# DRTS Mini-Project 2 — TSN Analysis & Simulation
**02225 Distributed Real-Time Systems | Technical University of Denmark (DTU)**

---

## Overview

This project provides a suite of tools for evaluating and visualizing Time-Sensitive Networking (TSN) experiments. It focuses on comparing two traffic scheduling mechanisms: **Strict Priority (SP)** and **Credit-Based Shaper (CBS)**.

The suite includes three tools: an analytical Worst-Case Response Time (WCRT) calculator, a discrete-event simulator, and a network topology visualizer. All tools read their configuration from structured JSON test cases located in the `TestCases/` directory.



## Project Structure

```text
DRTS-Mini-Project-2/
│
├── analysis.py                 # Compositional WCRT analytical calculator
├── simulation.py               # Discrete-event network simulator
├── Topology_visualization.py   # Network topology visualizer
├── README.md                   # This file
│
└── TestCases/                  # Subfolders containing JSON network configurations
    ├── test_case_1/
    ├── test_case_2/
    ├── test_case_3/
    ├── test_case_starvation/
    └── ...
```



## Requirements

Make sure you have **Python 3** installed along with the following libraries:

```bash
pip install matplotlib networkx numpy
```



## Input Data Format

All tools dynamically load their configuration from a specified folder inside `TestCases/`. A valid test case folder must contain:

| File | Description |
|------|-------------|
| `topology.json` | Defines nodes (end systems, switches), links, and bandwidths |
| `streams.json` | Defines traffic flows (ID, PCP priority, frame size, period, deadline) |
| `routes.json` | Maps each flow to its specific network path |
| `config.json` | Defines CBS slopes (idle/send rates). Defaults to `0.5` if missing |



## How to Run

Navigate to the `DRTS-Mini-Project-2/` directory and run any tool using the `--TestCase` flag.

---

### 1. Analytical Tool (`analysis.py`)

Computes the theoretical Worst-Case Response Time (WCRT) for each stream using compositional analysis across all links in the route, under both SP and CBS.

```bash
python analysis.py --TestCase <folder_name>
```

**Example:**

```bash
python analysis.py --TestCase test_case_1
```

Outputs a formatted table comparing SP WCRT and CBS WCRT in microseconds. Streams exceeding their deadline are flagged as `STARVED(value)`, where `value` is the computed WCRT that exceeded the deadline.

---

### 2. Simulation Tool (`simulation.py`)

Runs a discrete-event simulation tracking frame generation, queueing, and transmission over the network hyperperiod under both SP and CBS.

```bash
python simulation.py --TestCase <folder_name>
```

**Example:**

```bash
python simulation.py --TestCase test_case_starvation
```

Outputs the empirically observed maximum delay per stream under both SP and CBS. Streams that miss their deadline are flagged as `STARVED(value)`, where `value` is the maximum observed delay that exceeded the deadline.

---

### 3. Topology Visualizer (`Topology_visualization.py`)

Generates a clean diagram of the network topology, showing end systems, switches, link bandwidths, and propagation delays.

```bash
python Topology_visualization.py --TestCase <folder_name>
```

Use the `--save` flag to save the figure as a PNG instead of displaying it:

```bash
python Topology_visualization.py --TestCase test_case_1 --save
```

---

> If no `--TestCase` is provided, all three tools default to `TestCases/test_case_1`.

---

*Group 37 — Afonso Martim Domingues, Jeppe Weikop, Jonas Høyer, Tor Carlos Høydahl Ohme, William Allerup Carlsen*