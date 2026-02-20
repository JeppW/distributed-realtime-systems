from dataclasses import dataclass

@dataclass
class Task:
    id: int
    bcet: int
    wcet: int
    period: int
    deadline: int

    # RM priority: smaller period = higher priority (lower number)
    @property
    def rm_priority(self):
        return self.period


@dataclass
class Job:
    task_id: int
    release: int
    absolute_deadline: int
    remaining: int          # remaining WCET to execute
    completed: bool = False
    deadline_missed: bool = False