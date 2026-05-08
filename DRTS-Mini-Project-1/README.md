# DRTS Mini-Project 1 — Group 37
**02225 Distributed Real-Time Systems | Technical University of Denmark (DTU)**

---

## Overview

This project analyses and compares the schedulability and Worst-Case Response Times (WCRTs) of periodic task sets on a single processor core, using two real-time scheduling algorithms: **Deadline Monotonic (DM)** and **Earliest Deadline First (EDF)**.

Two software tools were developed: an analytical tool and a simulation tool. These were applied to a collection of task sets to validate theoretical models and explore the conditions under which EDF outperforms DM.


## Project Structure

```
DRTS-Mini-Project-1/
│
├── Analytical/       # Analytical tool for computing WCRTs and schedulability
├── Simulation/       # Simulation tool for empirically measuring response times
├── TestCases/        # CSV task set files used as input for both tools
│
└── README.md         # This file
```



## Folder Descriptions

### `Analytical/`
Contains the analytical tool, which evaluates the **theoretical schedulability** of a given task set and computes the WCRT for each task under both DM and EDF scheduling. The analysis is based on exact mathematical bounds — Response Time Analysis (RTA) for DM and Processor Demand Analysis for EDF.

> For instructions on how to run the analytical tool, see **`Analytical/README.md`**

---

### `Simulation/`
Contains the simulation tool, which implements both DM and EDF scheduling algorithms and **empirically measures response times** over the hyperperiod. Execution times can be sampled stochastically (Uniform or Beta distribution) or fixed at WCET for direct comparison with the analytical results.

> For instructions on how to run the simulation tool, see **`Simulation/README.md`**

---

### `TestCases/`
Contains all task set CSV files used as input for both tools, including the provided `automotive` and `uunifast` datasets, as well as additional custom test cases featuring constrained deadlines ($D < T$).

> If no test case is specified when running a tool, a default test case is used automatically.



## How to Run

Each tool has its own dedicated README with step-by-step run instructions. Both tools read task sets from the `TestCases/` folder.

| Tool       | Instructions              |
|------------|---------------------------|
| Analytical | `Analytical/README.md`    |
| Simulation | `Simulation/README.md`    |

---

*Group 37 — Afonso Martim Domingues, Jeppe Weikop, Jonas Høyer, Tor Carlos Høydahl Ohme, William Allerup Carlsen*