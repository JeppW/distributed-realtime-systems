import argparse
import os
from src.simulator import simulate, write_results
from src.utils import load_taskset
from src.visualize import visualize_trace, nice_visualization

def get_csv_filepath(dataset, partition, num):
    # The `output` folder was moved to be a sibling of the Simulation folder.
    # Compute the repository parent directory (one level above this script) and
    # use the sibling `output` directory as the new root for task-sets.
    repo_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    roots = {
        "automotive": os.path.join(repo_parent, "output", "automotive-utilDist", "automotive-perDist"),
        "uunifast": os.path.join(repo_parent, "output", "uunifast-utilDist", "uniform-discrete-perDist"),
    }

    prefixes = {
        "automotive": "automotive",
        "uunifast": "uniform-discrete",
    }

    base = roots[dataset]
    prefix = prefixes[dataset]
    csv = os.path.join(base, "1-core", "25-task", "0-jitter", partition, "tasksets", f"{prefix}_{num}.csv")
    return csv


def parse_args():
    parser = argparse.ArgumentParser(prog="simulator")
    parser.add_argument("mode", default="simulate", choices=["simulate", "gantt", "nice"], help="Mode: simulate or visualize")
    parser.add_argument("--dataset", default="automotive", choices=["automotive", "uunifast"], help="Pick a dataset root to search for the csv (overrides csv if found)")
    parser.add_argument("--partition", default="0.10-util", choices=[f"{i/100:.2f}-util" for i in range(10, 101, 10)], help="Choose dataset partition (e.g. 0.10-util)")
    parser.add_argument("--file-num", type=int, default=1, choices=[i for i in range(100)], help="filenumber in dataset partition")
    parser.add_argument("--policy", default="RM", choices=["RM", "DM", "EDF"], help="Scheduling policy")
    parser.add_argument("--runtime", default="uniform", choices=["wcet", "uniform", "beta"], help="How to choose job runtimes")
    # Default output directory: sibling `output` folder next to the Simulation folder
    default_output = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
    parser.add_argument("--output", default=default_output, help="Output directory")
    parser.add_argument("--trace-path", help="path to the trace CSV file to visualize")
    parser.add_argument("--trace-path-2", help="second trace CSV file to visualize")
    return parser.parse_args()

def main():
    args = parse_args()

    if args.mode == "gantt":
        # visualize, don't simulate
        if not args.trace_path or not os.path.exists(args.trace_path):
            print("Invalid trace path")
            exit()

        out_path = visualize_trace(args.trace_path)
        print(f"Results written to {out_path}")
        return

    elif args.mode == "simulate":
        # simulate
        csv = get_csv_filepath(args.dataset, args.partition, args.file_num)
        tasks = load_taskset(csv)
        print(f"Running simulation with {args.policy}... ", end="", flush=True)
        res = simulate(tasks, args.policy, runtime_model=args.runtime)
        print("Done!")
        print(f"Feasible schedule: {res['feasible']}")
        trace_path, summary_path = write_results(res, tasks, args.policy, args.output, str(args.file_num), args.dataset)
        print(f"Results written to {trace_path}")

    elif args.mode == "nice":
        out_path = nice_visualization(args.trace_path, args.trace_path_2)
        print(f"Results written to {out_path}")

if __name__ == "__main__":
    main()
