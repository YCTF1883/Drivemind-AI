from tortoise import fields

from .base import BaseModel, TimestampMixin
from .enums import ProjectStatus, ReportStatus, RiskLevel, TaskPriority, TaskSource, TaskStatus, TaskWorkload


class Project(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=100, description="项目名称", index=True)
    code = fields.CharField(max_length=50, description="项目编码", index=True)
    desc = fields.TextField(null=True, description="项目描述")
    status = fields.CharEnumField(ProjectStatus, default=ProjectStatus.ACTIVE, description="项目状态", index=True)
    start_date = fields.DateField(null=True, description="开始日期", index=True)
    end_date = fields.DateField(null=True, description="结束日期", index=True)
    progress = fields.IntField(default=0, description="项目进度", index=True)
    risk_level = fields.CharEnumField(RiskLevel, default=RiskLevel.LOW, description="风险等级", index=True)
    manager_id = fields.IntField(null=True, description="项目经理ID", index=True)
    creator_id = fields.IntField(description="创建人ID", index=True)
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)

    class Meta:
        table = "project"


class Task(BaseModel, TimestampMixin):
    title = fields.CharField(max_length=100, description="任务标题", index=True)
    desc = fields.TextField(null=True, description="任务描述")
    project_id = fields.IntField(description="所属项目ID", index=True)
    assignee_id = fields.IntField(null=True, description="负责人ID", index=True)
    creator_id = fields.IntField(description="创建人ID", index=True)
    priority = fields.CharEnumField(TaskPriority, default=TaskPriority.MEDIUM, description="优先级", index=True)
    due_date = fields.DateField(null=True, description="截止日期", index=True)
    status = fields.CharEnumField(TaskStatus, default=TaskStatus.NOT_STARTED, description="任务状态", index=True)
    progress = fields.IntField(default=0, description="任务进度", index=True)
    workload = fields.CharEnumField(TaskWorkload, default=TaskWorkload.NORMAL, description="任务工作量", index=True)
    risk_level = fields.CharEnumField(RiskLevel, default=RiskLevel.LOW, description="风险等级", index=True)
    source = fields.CharEnumField(TaskSource, default=TaskSource.MANUAL, description="任务来源", index=True)
    is_archived = fields.BooleanField(default=False, description="归档标记", index=True)

    class Meta:
        table = "task"


class TaskParticipant(BaseModel, TimestampMixin):
    task_id = fields.IntField(description="任务ID", index=True)
    user_id = fields.IntField(description="参与人ID", index=True)

    class Meta:
        table = "task_participant"
        unique_together = (("task_id", "user_id"),)


class WorkReport(BaseModel, TimestampMixin):
    task_id = fields.IntField(description="任务ID", index=True)
    reporter_id = fields.IntField(description="提交人ID", index=True)
    raw_content = fields.TextField(description="原始汇报内容")
    completed_items = fields.JSONField(default=list, description="完成事项")
    problems = fields.JSONField(default=list, description="遇到的问题")
    risk_level = fields.CharEnumField(RiskLevel, default=RiskLevel.LOW, description="风险等级", index=True)
    support_needed = fields.JSONField(default=list, description="所需支持")
    suggestions = fields.JSONField(default=list, description="建议动作")
    progress_delta = fields.IntField(default=0, description="系统估算进度变化")
    progress_after = fields.IntField(default=0, description="汇报后系统估算进度")
    status = fields.CharEnumField(ReportStatus, default=ReportStatus.CONFIRMED, description="汇报状态", index=True)

    class Meta:
        table = "work_report"


class ManagerQuery(BaseModel, TimestampMixin):
    question = fields.TextField(description="管理者问题")
    answer = fields.TextField(description="AI回答")
    evidences = fields.JSONField(default=list, description="引用证据")
    user_id = fields.IntField(description="提问人ID", index=True)

    class Meta:
        table = "manager_query"


class AIConversationMessage(BaseModel, TimestampMixin):
    session_id = fields.CharField(max_length=128, description="会话ID", index=True)
    user_id = fields.IntField(description="用户ID", index=True)
    role = fields.CharField(max_length=20, description="消息角色", index=True)
    content = fields.TextField(description="消息内容")
    metadata = fields.JSONField(default=dict, description="上下文元数据")

    class Meta:
        table = "ai_conversation_message"
