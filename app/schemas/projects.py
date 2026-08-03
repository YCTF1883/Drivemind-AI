from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ProjectStatus, RiskLevel


class BaseProject(BaseModel):
    name: str = Field(..., max_length=100, description="项目名称")
    code: str = Field(..., max_length=50, description="项目编码")
    desc: Optional[str] = Field(None, description="项目描述")
    status: ProjectStatus = Field(ProjectStatus.ACTIVE, description="项目状态")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    progress: int = Field(0, ge=0, le=100, description="项目进度")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="风险等级")
    manager_id: Optional[int] = Field(None, description="项目经理ID")

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("结束日期不能早于开始日期")
        return self


class ProjectCreate(BaseProject): ...


class ProjectUpdate(BaseProject):
    id: int


class ProjectQuery(BaseModel):
    name: str = ""
    code: str = ""
    status: Optional[ProjectStatus] = None
    risk_level: Optional[RiskLevel] = None
    manager_id: Optional[int] = None
