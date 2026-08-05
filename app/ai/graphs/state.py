from typing import Any, TypedDict

from app.models.admin import User
from app.models.business import Project, Task
from app.schemas.ai import ProjectWeeklyReportRequest, TaskBreakdownRequest


class TaskBreakdownState(TypedDict, total=False):
    req: TaskBreakdownRequest
    prompt: str
    raw_result: dict[str, Any]
    result: dict[str, Any]


class ReportAnalysisState(TypedDict, total=False):
    task: Task
    content: str
    task_data: dict[str, Any]
    prompt: str
    raw_result: dict[str, Any]
    result: dict[str, Any]


class ProjectWeeklyReportState(TypedDict, total=False):
    req: ProjectWeeklyReportRequest
    user: User
    project: Project
    tasks: list[Task]
    reports: list[Any]
    project_data: dict[str, Any]
    task_data: list[dict[str, Any]]
    report_data: list[dict[str, Any]]
    analysis: dict[str, Any]
    risks: list[dict[str, Any]]
    report_summaries: list[str]
    prompt: str
    raw_result: dict[str, Any]
    result: dict[str, Any]


class ManagerQAState(TypedDict, total=False):
    user: User
    question: str
    context_messages: list[dict]
    is_management_question: bool
    evidences: list[dict]
    filtered_evidences: list[dict]
    raw_result: dict[str, Any]
    result: dict[str, Any]
