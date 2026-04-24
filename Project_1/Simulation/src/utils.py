import csv
from math import gcd
from functools import reduce
from typing import List
from src.models import Task

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)

def hyperperiod(tasks: List[Task]) -> int:
    return reduce(lcm, (t.period for t in tasks))

def load_taskset(csv_path: str) -> List[Task]:
    tasks = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(Task(
                id=int(row["TaskID"]),
                bcet=int(row["BCET"]),
                wcet=int(row["WCET"]),
                period=int(row["Period"]),
                deadline=int(row["Deadline"]),
            ))
    return tasks