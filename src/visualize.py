import csv
import os
from typing import Optional
import matplotlib.pyplot as plt


def _task_color(task_id: int):
    cmap = plt.cm.get_cmap("tab20")
    return cmap(task_id % 20)


def _load_trace(trace_path: str):
    """Return list of (start, end, task_id_or_None)."""
    segments = []
    with open(trace_path, newline="") as f:
        for row in csv.DictReader(f):
            tid = None if row["TaskID"] == "IDLE" else int(row["TaskID"])
            segments.append((int(row["Start"]), int(row["End"]), tid))
    return segments


def _plot_gantt(segments, title: str, ax):
    task_ids = sorted({s[2] for s in segments if s[2] is not None})
    y_map = {tid: i for i, tid in enumerate(task_ids)}

    for start, end, tid in segments:
        if tid is None:
            continue
        end_draw = end
        y = y_map[tid]
        ax.barh(y, end_draw - start, left=start, height=0.6,
                color=_task_color(tid), edgecolor="black", linewidth=0.3)

    ax.set_yticks(range(len(task_ids)))
    ax.set_yticklabels([f"Task {tid}" for tid in task_ids])
    ax.set_xlabel("Time")
    ax.set_title(title)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)


def visualize_trace(trace_csv_path: str, out_path: Optional[str] = None):
    if not os.path.exists(trace_csv_path):
        raise FileNotFoundError(trace_csv_path)

    segments = _load_trace(trace_csv_path)
    if not segments:
        raise ValueError("Trace file is empty or malformed")

    fig, ax = plt.subplots(figsize=(16, max(2, len({s[2] for s in segments if s[2] is not None}) * 0.5)))
    base = os.path.splitext(os.path.basename(trace_csv_path))[0]
    _plot_gantt(segments, base, ax)
    plt.tight_layout()

    if out_path is None:
        out_path = os.path.join(os.path.dirname(trace_csv_path), f"{base}_gantt.png")

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path

