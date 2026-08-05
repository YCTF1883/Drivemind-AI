from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import RiskLevel, TaskPriority, TaskWorkload
from app.schemas.reports import ReportAnalysisResult


class TaskBreakdownRequest(BaseModel):
    project_id: Optional[int] = Field(None, description="已有项目ID")
    goal: str = Field(..., min_length=1, description="项目目标")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    assignee_ids: list[int] = Field(default_factory=list, description="候选负责人ID")


class TaskBreakdownItem(BaseModel):
    title: str = Field(..., description="任务标题")
    desc: str = Field("", description="任务描述")
    assignee_id: Optional[int] = Field(None, description="推荐负责人ID")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="优先级")
    workload: TaskWorkload = Field(TaskWorkload.NORMAL, description="任务工作量")
    due_date: Optional[date] = Field(None, description="截止日期")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")


class TaskBreakdownResult(BaseModel):
    tasks: list[TaskBreakdownItem] = Field(default_factory=list, description="拆解任务")
    summary: str = Field("", description="拆解说明")


class ManagerQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="管理者问题")
    session_id: Optional[str] = Field(None, description="问答会话ID")


class ManagerAnswerResult(BaseModel):
    answer: str = Field(..., description="AI回答")
    evidences: list[dict] = Field(default_factory=list, description="引用证据")


class ProjectWeeklyReportRequest(BaseModel):
    project_id: int = Field(..., description="项目ID")
    start_date: Optional[date] = Field(None, description="周报开始日期")
    end_date: Optional[date] = Field(None, description="周报结束日期")


class ProjectWeeklyReportResult(BaseModel):
    title: str = Field(..., description="周报标题")
    project_name: str = Field(..., description="项目名称")
    project_code: str = Field("", description="项目编码")
    period: str = Field(..., description="统计周期")
    overall_summary: str = Field(..., description="整体总结")
    progress_summary: str = Field(..., description="进度总结")
    completed_work: list[str] = Field(default_factory=list, description="已完成工作")
    ongoing_tasks: list[str] = Field(default_factory=list, description="进行中任务")
    blocked_or_risky_items: list[str] = Field(default_factory=list, description="风险与阻塞事项")
    recent_reports_summary: list[str] = Field(default_factory=list, description="近期汇报摘要")
    next_week_plan: list[str] = Field(default_factory=list, description="下周计划")
    management_suggestions: list[str] = Field(default_factory=list, description="管理建议")
    evidences: list[dict] = Field(default_factory=list, description="引用证据")


__all__ = [
    "ReportAnalysisResult",
    "TaskBreakdownRequest",
    "TaskBreakdownItem",
    "TaskBreakdownResult",
    "ManagerQuestionRequest",
    "ProjectWeeklyReportRequest",
    "ProjectWeeklyReportResult",
]
