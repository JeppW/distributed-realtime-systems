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

def _plot_colored_timeline(segments, y, ax, idle_color="lightgray"):
    for start, end, tid in segments:
        if tid is None:
            color = idle_color
        else:
            color = _task_color(tid)
        # Use a much thicker line so the timeline is visually more prominent.
        ax.hlines(y, start, end, colors=color, linewidth=28)


def nice_visualization(edf_trace_path: str, dm_trace_path: str, out_path: Optional[str] = None):
    if not os.path.exists(edf_trace_path):
        raise FileNotFoundError(edf_trace_path)
    if not os.path.exists(dm_trace_path):
        raise FileNotFoundError(dm_trace_path)

    edf_segments = _load_trace(edf_trace_path)
    dm_segments = _load_trace(dm_trace_path)

    if not edf_segments or not dm_segments:
        raise ValueError("Trace file is empty or malformed")

    all_tasks = sorted({s[2] for s in edf_segments + dm_segments if s[2] is not None})

    # Keep the figure a reasonable height: two lines only, so we don't need a tall figure.
    fig, ax = plt.subplots(figsize=(16, 3))
    _plot_colored_timeline(edf_segments, 1.0, ax)
    _plot_colored_timeline(dm_segments, 0.0, ax)

    ax.set_yticks([1.0, 0.0])
    ax.set_yticklabels(["EDF", "DM"], fontsize=12)
    ax.set_ylim(-0.5, 1.5)
    ax.set_xlabel("Time", fontsize=13)
    ax.set_title("EDF vs DM timeline")
    ax.grid(axis="x", alpha=0.3)

    # Legend for tasks
    from matplotlib.patches import Patch

    legend_patches = [Patch(color=_task_color(tid), label=f"Task {tid}") for tid in all_tasks]
    if legend_patches:
        ax.legend(
            handles=legend_patches,
            title="Tasks",
            bbox_to_anchor=(1.02, 1.0),
            loc="upper left",
            ncol=1,
            fontsize=11,
            title_fontsize=12,
        )

    # Determine x limits
    start_times = [s[0] for s in edf_segments + dm_segments]
    end_times = [s[1] for s in edf_segments + dm_segments]
    ax.set_xlim(min(start_times), max(end_times))

    plt.tight_layout()

    base = os.path.splitext(os.path.basename(edf_trace_path))[0]
    if out_path is None:
        out_path = os.path.join(os.path.dirname(edf_trace_path), f"{base}_nice.png")

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path

