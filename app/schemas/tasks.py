from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import RiskLevel, TaskPriority, TaskSource, TaskStatus


class BaseTask(BaseModel):
    title: str = Field(..., max_length=100, description="任务标题")
    desc: Optional[str] = Field(None, description="任务描述")
    project_id: int = Field(..., description="所属项目ID")
    assignee_id: Optional[int] = Field(None, description="负责人ID")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="优先级")
    due_date: Optional[date] = Field(None, description="截止日期")
    status: TaskStatus = Field(TaskStatus.NOT_STARTED, description="任务状态")
    progress: int = Field(0, ge=0, le=100, description="任务进度")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")
    source: TaskSource = Field(TaskSource.MANUAL, description="任务来源")

    @model_validator(mode="after")
    def validate_completed_progress(self):
        if self.status == TaskStatus.COMPLETED and self.progress != 100:
            raise ValueError("已完成任务的进度必须为100")
        return self


class TaskCreate(BaseTask): ...


class TaskUpdate(BaseTask):
    id: int


class TaskProgressUpdate(BaseModel):
    id: int
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(..., ge=0, le=100, description="任务进度")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")

    @model_validator(mode="after")
    def validate_completed_progress(self):
        if self.status == TaskStatus.COMPLETED and self.progress != 100:
            raise ValueError("已完成任务的进度必须为100")
        return self


class TaskBatchCreate(BaseModel):
    tasks: list[TaskCreate] = Field(..., min_length=1, description="任务列表")


class TaskQuery(BaseModel):
    title: str = ""
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    risk_level: Optional[RiskLevel] = None
    priority: Optional[TaskPriority] = None
