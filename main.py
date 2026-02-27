import argparse
import os
from src.simulator import simulate, write_results
from src.utils import load_taskset
from src.visualize import visualize_trace

def parse_args():
    parser = argparse.ArgumentParser(prog="simulator")
    parser.add_argument("--dataset", default="automotive", choices=["automotive", "uunifast"], help="Pick a dataset root to search for the csv (overrides csv if found)")
    parser.add_argument("--partition", default="0.10-util", choices=[f"{i/100:.2f}-util" for i in range(10, 101, 10)], help="Choose dataset partition (e.g. 0.10-util)")
    parser.add_argument("--file-num", type=int, default=1, choices=[i for i in range(100)], help="filenumber in dataset partition")
    parser.add_argument("--policy", default="RM", help="Scheduling policy (EDF or RM)")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--visualize", action="store_true", default=False, help="Visualize instead of simulate")
    parser.add_argument("--trace-path", help="path to the trace CSV file to visualize")
    return parser.parse_args()

def get_csv_filepath(dataset, partition, num):
    roots = {
        "automotive": os.path.join("task-sets", "output", "automotive-utilDist", "automotive-perDist"),
        "uunifast": os.path.join("task-sets", "output", "uunifast-utilDist", "uniform-discrete-perDist"),
    }

    base = roots[dataset]
    csv = os.path.join(base, "1-core", "25-task", "0-jitter", partition, "tasksets", f"{dataset}_{num}.csv")
    return csv

def main():
    args = parse_args()

    if args.visualize:
        # visualize
        if not args.trace_path or not os.path.exists(args.trace_path):
            print("Invalid trace path")
            exit()

        out_path = visualize_trace(args.trace_path)
        print(f"Results written to {out_path}")
        return

    # simulate
    csv = get_csv_filepath(args.dataset, args.partition, args.file_num)
    tasks = load_taskset(csv)
    print(f"Running simulation with {args.policy}... ", end="", flush=True)
    res = simulate(tasks, args.policy)
    print("Done!")
    print(f"Feasible schedule: {res['feasible']}")
    trace_path, summary_path = write_results(res, tasks, args.policy, "output", str(args.file_num), args.dataset)
    print(f"Results written to {trace_path}")

if __name__ == "__main__":
    main()
