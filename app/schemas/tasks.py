from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.controllers.progress import task_status_progress
from app.models.enums import RiskLevel, TaskPriority, TaskSource, TaskStatus, TaskWorkload


class BaseTask(BaseModel):
    title: str = Field(..., max_length=100, description="任务标题")
    desc: Optional[str] = Field(None, description="任务描述")
    project_id: int = Field(..., description="所属项目ID")
    assignee_id: Optional[int] = Field(None, description="负责人ID")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="优先级")
    due_date: Optional[date] = Field(None, description="截止日期")
    status: TaskStatus = Field(TaskStatus.NOT_STARTED, description="任务状态")
    progress: int = Field(0, ge=0, le=100, description="系统估算进度")
    workload: TaskWorkload = Field(TaskWorkload.NORMAL, description="任务工作量")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")
    source: TaskSource = Field(TaskSource.MANUAL, description="任务来源")

    @model_validator(mode="after")
    def set_status_progress(self):
        self.progress = task_status_progress(self.status)
        return self


class TaskCreate(BaseTask): ...


class TaskUpdate(BaseTask):
    id: int


class TaskProgressUpdate(BaseModel):
    id: int
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(0, ge=0, le=100, description="系统估算进度")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")

    @model_validator(mode="after")
    def set_status_progress(self):
        allowed_statuses = {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.IN_REVIEW}
        if self.status not in allowed_statuses:
            raise ValueError("员工只能将任务更新为进行中、阻塞或审核中")
        self.progress = task_status_progress(self.status)
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
