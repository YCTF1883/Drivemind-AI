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


__all__ = [
    "ReportAnalysisResult",
    "TaskBreakdownRequest",
    "TaskBreakdownItem",
    "TaskBreakdownResult",
    "ManagerQuestionRequest",
    "ManagerAnswerResult",
]
