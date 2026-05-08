# Simulation Tool — README
**02225 Distributed Real-Time Systems | Technical University of Denmark (DTU)**

---

## Overview

This tool simulates preemptive real-time scheduling over one hyperperiod and empirically measures response times for each task. It supports three scheduling policies: **Rate Monotonic (RM)**, **Deadline Monotonic (DM)**, and **Earliest Deadline First (EDF)**.

Job execution times can be sampled stochastically or fixed at WCET for direct comparison with analytical results. The tool outputs a schedule trace and a summary, and can generate Gantt chart visualizations.



## Project Structure

```
Simulation/
│
├── simulation.py       # Entry point — run this
└── src/
    ├── models.py       # Task and Job dataclasses
    ├── simulator.py    # Core simulation logic
    ├── utils.py        # Hyperperiod calculation and CSV loader
    └── visualize.py    # Gantt chart and timeline visualization
```



## Requirements

Make sure you have **Python 3** installed along with the following library:

```bash
pip install matplotlib
```

All other dependencies (`csv`, `os`, `json`, `random`, `math`, `argparse`) are part of the Python standard library.


## How to Run

cNavigate to the `Simulation/` folder. The tool has three modes: `simulate`, `gantt`, and `vizualize`.



### Mode 1 — `simulate` (run the scheduler)

```bash
python simulation.py simulate --dataset <dataset> --partition <partition> --file-num <num> --policy <policy> --runtime <runtime>
```

| Argument      | Options                             | Default        |
|---------------|-------------------------------------|----------------|
| `--dataset`   | `automotive`, `uunifast`            | `automotive`   |
| `--partition` | `0.10-util` ... `1.00-util`         | `0.10-util`    |
| `--file-num`  | `0` ... `99`                        | `1`            |
| `--policy`    | `RM`, `DM`, `EDF`                   | `RM`           |
| `--runtime`   | `wcet`, `uniform`, `beta`           | `uniform`      |
| `--output`    | Path to output directory            | `/output`    |

**Example:**

```bash
python simulation.py simulate --dataset uunifast --partition 0.90-util --file-num 2 --policy EDF --runtime beta
```

This will produce two output files in the `output/` folder:
- `<dataset>_<num>_<policy>_trace.csv` — full schedule trace
- `<dataset>_<num>_<policy>_summary.json` — summary with feasibility, deadline misses, and utilization

---

### Mode 2 — `gantt` (visualize a single trace)

Generates a Gantt chart from a previously saved trace file:

```bash
python simulation.py gantt --trace-path <path-to-trace.csv>
```

**Example:**

```bash
python simulation.py gantt --trace-path output/uunifast_2_EDF_trace.csv
```

---

### Mode 3 — `vizualize` (compare EDF vs DM side by side)

Generates a combined EDF vs DM timeline visualization from two trace files:

```bash
python simulation.py vizualize --trace-path <edf-trace.csv> --trace-path-2 <dm-trace.csv>
```

**Example:**

```bash
python simulation.py vizualize --trace-path output/uunifast_2_EDF_trace.csv --trace-path-2 output/uunifast_2_DM_trace.csv
```


## Runtime Models

| Model     | Description                                                                 |
|-----------|-----------------------------------------------------------------------------|
| `wcet`    | All jobs execute at their Worst-Case Execution Time (deterministic)         |
| `uniform` | Execution time sampled uniformly between BCET and WCET                      |
| `beta`    | Execution time sampled from a scaled Beta distribution, skewed towards BCET |

Use `wcet` mode to directly compare simulation results against the analytical tool output.


## Notes

- The simulation runs for exactly one hyperperiod.
- If a job misses its deadline, it is removed from the queue and the schedule is marked as infeasible.
- Task set CSV files are read from the `TestCases/` folder (sibling of `Simulation/`).