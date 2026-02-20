import argparse
from src.simulator import simulate, write_results
from src.utils import load_taskset
from src.visualize import visualize_trace

def parse_args():
    parser = argparse.ArgumentParser(prog="simulator")
    parser.add_argument("csv", help="Path to taskset/trace CSV")
    parser.add_argument("--policy", default="RM", help="Scheduling policy (EDF or RM)")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--name", default="1", help="Prefix to name output file")
    parser.add_argument("--visualize", action="store_true", default=False, help="Visualize instead of simulate")
    return parser.parse_args()

def main():
    args = parse_args()

    if args.visualize:
        out_path = visualize_trace(args.csv)
        print(f"Results written to {out_path}")
        return
        
    # simulate mode
    tasks = load_taskset(args.csv)
    print(f"Running simulation with {args.policy}... ", end="", flush=True)
    res = simulate(tasks, args.policy)
    print("Done!")
    print(f"Feasible schedule: {res['feasible']}")
    trace_path, summary_path = write_results(res, tasks, args.policy, "output", "1")
    print(f"Results written to {trace_path}")

if __name__ == "__main__":
    main()
