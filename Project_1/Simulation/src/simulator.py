import csv
import os
import json
import random
from typing import List
from src.models import Task, Job
from src.utils import hyperperiod

def _choose_job_runtime(task, model) -> int:
    if model == "wcet":
        return task.wcet
    elif model == "uniform":
        return random.randint(task.bcet, task.wcet)
    elif model == "beta":
        # scaled beta
        r = random.betavariate(1.3, 2.3)   # parameters chosen with https://homepage.divms.uiowa.edu/~mbognar/applets/beta.html
        return task.bcet + int(r * (task.wcet - task.bcet))

    else:
        raise RuntimeError(f"Unsupported runtime model: {model}")


def simulate(tasks: List[Task], policy: str, runtime_model="uniform"):
    """Simulate preemptive scheduling for one hyperperiod."""
    hp = hyperperiod(tasks)

    active_jobs: List[Job] = []
    schedule: list = []          # (start, end, task_id | None)
    deadline_misses: list = []

    current_task_id = None
    segment_start = 0

    for t in range(hp):
        # 1. Release new jobs at time t
        for task in tasks:
            if t % task.period == 0:
                active_jobs.append(Job(
                    task_id=task.id,
                    release=t,
                    absolute_deadline=t + task.deadline,
                    remaining=_choose_job_runtime(task, runtime_model),
                ))

        # 2. Check deadline misses for jobs whose deadline is now
        for job in active_jobs:
            if job.absolute_deadline == t and job.remaining > 0:
                job.deadline_missed = True
                deadline_misses.append((job.task_id, job.release, job.absolute_deadline))

        # Remove completed or deadline-missed jobs
        active_jobs = [j for j in active_jobs if j.remaining > 0 and not j.deadline_missed]

        # 3. Select highest-priority ready job
        if active_jobs:
            if policy == "RM":
                # Static priority: smallest period wins; break ties by task id
                task_map = {task.id: task for task in tasks}
                best = min(active_jobs, key=lambda j: (task_map[j.task_id].rm_priority, j.task_id))
            elif policy == "DM":
                task_map = {task.id: task for task in tasks}
                best = min(active_jobs, key=lambda j: (task_map[j.task_id].dm_priority, j.task_id))
            elif policy == "EDF":
                best = min(active_jobs, key=lambda j: (j.absolute_deadline, j.task_id))
            else:
                raise RuntimeError("Unsupported policy!")

            chosen_id = best.task_id
            best.remaining -= 1

            if best.remaining == 0:
                best.completed = True
        else:
            chosen_id = None

        # 4. Record schedule (merge consecutive identical segments)
        if chosen_id != current_task_id:
            if t > segment_start:
                schedule.append((segment_start, t, current_task_id))
            segment_start = t
            current_task_id = chosen_id

    # Close last segment
    if hp > segment_start:
        schedule.append((segment_start, hp, current_task_id))

    return {
        "schedule": schedule,
        "deadline_misses": deadline_misses,
        "feasible": len(deadline_misses) == 0,
        "hyperperiod": hp,
    }


def write_results(results: dict, tasks: List[Task], policy: str, out_dir: str, filenum: str, dataset: str):
    os.makedirs(out_dir, exist_ok=True)
    base = f"{dataset}_{filenum}_{policy}"

    # 1. Schedule trace CSV
    trace_path = os.path.join(out_dir, f"{base}_trace.csv")
    with open(trace_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Start", "End", "TaskID"])
        for start, end, tid in results["schedule"]:
            w.writerow([start, end, tid if tid is not None else "IDLE"])

    # 2. Summary JSON
    summary = {
        "policy": policy,
        "taskset": f"{dataset}/{filenum}",
        "num_tasks": len(tasks),
        "hyperperiod": results["hyperperiod"],
        "feasible": results["feasible"],
        "num_deadline_misses": len(results["deadline_misses"]),
        "deadline_misses": [
            {"task_id": m[0], "release": m[1], "deadline": m[2]}
            for m in results["deadline_misses"]
        ],
        "utilization": sum(t.wcet / t.period for t in tasks),
    }
    summary_path = os.path.join(out_dir, f"{base}_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    return trace_path, summary_path
