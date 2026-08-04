from app.models.enums import TaskStatus, TaskWorkload


STATUS_PROGRESS = {
    TaskStatus.NOT_STARTED: 0,
    TaskStatus.BLOCKED: 30,
    TaskStatus.IN_PROGRESS: 50,
    TaskStatus.IN_REVIEW: 80,
    TaskStatus.COMPLETED: 100,
    TaskStatus.ARCHIVED: 0,
}

WORKLOAD_WEIGHT = {
    TaskWorkload.SIMPLE: 1,
    TaskWorkload.NORMAL: 2,
    TaskWorkload.COMPLEX: 3,
}


def task_status_progress(status: TaskStatus | str | None) -> int:
    if status is None:
        return STATUS_PROGRESS[TaskStatus.NOT_STARTED]
    try:
        status = TaskStatus(status)
    except ValueError:
        return STATUS_PROGRESS[TaskStatus.NOT_STARTED]
    return STATUS_PROGRESS[status]


def task_workload_value(workload: TaskWorkload | str | None) -> int:
    if workload is None:
        return WORKLOAD_WEIGHT[TaskWorkload.NORMAL]
    try:
        workload = TaskWorkload(workload)
    except ValueError:
        return WORKLOAD_WEIGHT[TaskWorkload.NORMAL]
    return WORKLOAD_WEIGHT[workload]
