# Project_2 — TSN Analysis & Simulation

Short description
-----------------
This folder contains two small tools for Time-Sensitive Networking (TSN) experiments:

- `analysis.py` — a compositional worst-case response time (WCRT) calculator. It computes per-stream WCRTs using Strict Priority (SP) and a simple Credit-Based Shaper (CBS) model across each link in a route.
- `simulation.py` — a discrete-event simulator that models packet generation, queueing, SP and CBS behaviour, and reports observed maximum delays (worst-case delays) or starvation.

Both scripts read test-case JSON files from a subfolder (defaults to `test_case_2`).

Repository layout (relevant files)
---------------------------------

- `analysis.py` — compositional WCRT analysis. Prints a table of SP and CBS WCRTs.
- `simulation.py` — event-driven simulation that prints per-stream maximum delays.
- `test_case_* /` — folders containing `topology.json`, `streams.json`, `routes.json`, and optionally `config.json` used as input.

Quick start
-----------
1. Open a terminal in this folder:

```bash
cd /home/william/Desktop/realtime/Project-1/Project_2
```

2. Run the static analysis:

```bash
python3 analysis.py
```

3. Run the discrete-event simulator:

```bash
python3 simulation.py
```

Notes on inputs
---------------
- By default both scripts use the constant `DIRECTORY = "test_case_2"` (near the top of each file). That directory must contain at least:
  - `topology.json` (contains `topology` with `links` and optional `default_bandwidth_mbps`)
  - `streams.json` (list of streams with `id`, `PCP`, `size`, `period`)
  - `routes.json` (routes mapping flows to hop lists)

- `simulation.py` optionally reads `config.json` (CBS slopes). If `config.json` is missing, default slopes of 0.5 are used.

Switching test cases
--------------------
- Edit the `DIRECTORY` constant at the top of `analysis.py` and/or `simulation.py` to the desired folder name (e.g., `test_case_1`).

What the scripts print
----------------------
- `analysis.py` prints a table with columns: Stream ID, SP WCRT, CBS WCRT (values in microseconds).
- `simulation.py` prints a table with stream size, PCP, period, SP worst-case delay (observed), CBS worst-case delay (observed), or `STARVED` if no frames finished for a stream.

Troubleshooting
---------------
- FileNotFoundError for `topology.json` / `streams.json` / `routes.json`: make sure the `DIRECTORY` constant matches a folder under this directory and that the JSON files exist.
- Python version: use Python 3 (3.8+ recommended). The code uses only the standard library.
- If a simulation run appears to produce no output or exits early: check that streams in `streams.json` have valid `period` and `size` values and that `routes.json` maps flow ids to valid paths.
