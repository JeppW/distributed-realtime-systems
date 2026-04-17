# Project 1 - Distributed Real-Time Systems
This is a simulation tool developed by Group 37 for Mini-Project 1 in 02225 Distributed Real-Time Systems.

The tool is written in Python and tested on Python 3.13.

## Example usage
Simulate RM on `automotive/0.10-util/1` with uniform runtime distribution.

```
python main.py simulate --dataset automotive --partition 0.10-util --file-num 1 --policy RM --runtime uniform
```

Simulate EDF on `uunifast/0.50-util/2` with beta runtime distribution.
```
python main.py simulate --dataset uunifast --partition 0.50-util --file-num 2 --policy EDF --runtime beta
```

Visualize schedule with Gantt diagram (run this on the generated csv file **after** simulation).

```
python main.py gantt --trace-path output/automotive_0_EDF_trace.csv
```

Compare the schedules of two runs (useful for comparing EDF and DM).
```
python main.py nice --trace-path output/automotive_0_EDF_trace.csv --trace-path-2 output/automotive_0_DM_trace.csv.csv
```

Get help with command-line options.

```
python main.py -h
```
