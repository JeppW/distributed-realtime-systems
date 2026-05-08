# Analytical Tool — README
**02225 Distributed Real-Time Systems | Technical University of Denmark (DTU)**

---

## Overview

This tool evaluates the **theoretical schedulability** of a real-time task set and computes the Worst-Case Response Time (WCRT) for each task under both **Deadline Monotonic (DM)** and **Earliest Deadline First (EDF)** scheduling algorithms.

It outputs a formatted table of WCRTs per task and generates a comparison graph.

## Project Structure

```
Analytical/
│
├── analytical.py               # Entry point — run this
├── task-set-examples.csv       # Default task set for quick tests
└── README.md                   # This file
```

## Requirements

Make sure you have **Python 3** installed along with the following library:

```bash
pip install matplotlib
```

All other dependencies (`math`, `csv`, `heapq`, `os`, `argparse`) are part of the Python standard library.


## Input Format

The tool reads `.csv` task set files from the `TestCases/` folder. The CSV file must have the following columns:

| Column     | Description                        |
|------------|------------------------------------|
| `TaskID`   | Unique integer identifier per task |
| `Jitter`   | Release jitter                     |
| `BCET`     | Best-Case Execution Time           |
| `WCET`     | Worst-Case Execution Time          |
| `Period`   | Task period                        |
| `Deadline` | Relative deadline                  |


## How to Run

Navigate to the `Analytical/` folder and run the tool using one of the three modes below.

### Default — Run with the built-in example task set

Running the tool with no arguments will automatically use the built-in default task set (`task-set-example.csv`):

```bash
python analytical.py
```

### Option 1 — Select from the standard datasets (recommended)

```bash
python analytical.py --dataset <dataset> --partition <partition> --file-num <num>
```

| Argument      | Options                                      | Default        |
|---------------|----------------------------------------------|----------------|
| `--dataset`   | `automotive`, `uunifast`                     | `automotive`   |
| `--partition` | `0.10-util` ... `1.00-util`                  | `0.10-util`    |
| `--file-num`  | `0` ... `99`                                 | `1`            |

**Example:**

```bash
python analytical.py --dataset uunifast --partition 0.90-util --file-num 2
```

---

### Option 2 — Provide a custom CSV file

Use the `--file` flag to point directly to any CSV file, overriding the dataset selection above:

```bash
python analytical.py --file ../TestCases/my-custom-taskset.csv
```
**Example:**

```bash
python analytical.py --file ../TestCases/automotive-utilDist/automotive-perDist/1-core/25-task/0-jitter/0.10-util/tasksets/automotive_1.csv
```


## Output

The tool will print to the terminal:

- Processor utilization `Up`
- Hyperperiod
- Schedulability result for DM and EDF
- A formatted table of WCRTs per task for both algorithms

It will also open a **comparison graph** plotting the DM WCRT, EDF WCRT, and deadline per task.

**Example output:**

```
============================================================
Analyzing Task Set: uunifast -- 0.90-util -- file 2
============================================================

Processor Utilization (Up) : 0.8500
Hyper Period               : 200000

Calculating Analytical WCRTs (Math)...
 -> RESULT: Task set IS schedulable using DM
 -> RESULT: Task set IS schedulable using EDF

+---------+-----------+-----------+-------------+-------------+
| Task ID | Period    | Deadline  | DM WCRT     | EDF WCRT    |
+---------+-----------+-----------+-------------+-------------+
| 0       | 5000      | 5000      | 4500        | 4500        |
| 1       | 4000      | 4000      | 5480        | 5480        |
+---------+-----------+-----------+-------------+-------------+
```


## Notes

- If `Up > 1`, the tool will immediately flag the task set as unschedulable and stop.
- The tool assumes `D <= T` for all tasks (relative deadline does not exceed the period).
- The `--file` flag overrides `--dataset`, `--partition`, and `--file-num` if provided together.
- Task set CSV files are read from the `TestCases/` folder (sibling of `Analytical/`).