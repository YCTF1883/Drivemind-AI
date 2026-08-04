from pydantic import BaseModel, Field, model_validator

from app.models.enums import ReportStatus, RiskLevel, TaskStatus


class ReportAnalysisResult(BaseModel):
    completed_items: list[str] = Field(default_factory=list, description="完成事项")
    problems: list[str] = Field(default_factory=list, description="遇到的问题")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")
    support_needed: list[str] = Field(default_factory=list, description="所需支持")
    suggestions: list[str] = Field(default_factory=list, description="建议动作")
    progress_delta: int = Field(0, ge=0, le=100, description="系统估算进度变化")
    progress_after: int = Field(0, ge=0, le=100, description="汇报后系统估算进度")


class ReportAnalyzeRequest(BaseModel):
    task_id: int = Field(..., description="任务ID")
    content: str = Field(..., min_length=1, description="自然语言汇报")


class ReportCreate(BaseModel):
    task_id: int = Field(..., description="任务ID")
    raw_content: str = Field(..., min_length=1, description="原始汇报内容")
    completed_items: list[str] = Field(default_factory=list, description="完成事项")
    problems: list[str] = Field(default_factory=list, description="遇到的问题")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")
    support_needed: list[str] = Field(default_factory=list, description="所需支持")
    suggestions: list[str] = Field(default_factory=list, description="建议动作")
    progress_delta: int = Field(0, ge=0, le=100, description="系统估算进度变化")
    progress_after: int = Field(0, ge=0, le=100, description="汇报后系统估算进度")
    status: ReportStatus = Field(ReportStatus.CONFIRMED, description="汇报状态")
    task_status: TaskStatus | None = Field(None, description="汇报后任务状态")

    @model_validator(mode="after")
    def validate_task_status(self):
        allowed_statuses = {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.IN_REVIEW}
        if self.task_status and self.task_status not in allowed_statuses:
            raise ValueError("汇报只能将任务更新为进行中、阻塞或审核中")
        return self


class ReportQuery(BaseModel):
    task_id: int | None = None
    reporter_id: int | None = None
    risk_level: RiskLevel | None = None
