import json
from datetime import date, datetime, time, timedelta
from typing import Any

from langgraph.graph import END, StateGraph
from tortoise.expressions import Q

from app.ai.exceptions import AIServiceError
from app.controllers.project import project_controller
from app.models.admin import User
from app.models.business import Task, TaskParticipant, WorkReport
from app.models.enums import RiskLevel, TaskStatus
from app.schemas.ai import ProjectWeeklyReportRequest, ProjectWeeklyReportResult
from app.settings.config import settings

from .llm import call_deepseek_json
from .state import ProjectWeeklyReportState


class ProjectWeeklyReportGraph:
    def __init__(self):
        graph = StateGraph(ProjectWeeklyReportState)
        graph.add_node("collect_project_context", self.collect_project_context)
        graph.add_node("analyze_progress", self.analyze_progress)
        graph.add_node("analyze_risks", self.analyze_risks)
        graph.add_node("summarize_reports", self.summarize_reports)
        graph.add_node("generate_report", self.generate_report)
        graph.add_node("validate_result", self.validate_result)
        graph.set_entry_point("collect_project_context")
        graph.add_edge("collect_project_context", "analyze_progress")
        graph.add_edge("analyze_progress", "analyze_risks")
        graph.add_edge("analyze_risks", "summarize_reports")
        graph.add_edge("summarize_reports", "generate_report")
        graph.add_edge("generate_report", "validate_result")
        graph.add_edge("validate_result", END)
        self.graph = graph.compile()

    async def run(self, req: ProjectWeeklyReportRequest, user: User) -> ProjectWeeklyReportResult:
        state = await self.graph.ainvoke({"req": req, "user": user})
        return ProjectWeeklyReportResult.model_validate(state["result"])

    async def collect_project_context(self, state: ProjectWeeklyReportState) -> ProjectWeeklyReportState:
        req = state["req"]
        project = await project_controller.get_visible(req.project_id, state["user"])
        tasks = await Task.filter(project_id=project.id, is_archived=False).order_by("risk_level", "due_date", "-updated_at")
        task_ids = [task.id for task in tasks]

        report_q = Q(task_id__in=task_ids)
        start_date, end_date = self.resolve_period(req)
        if start_date:
            report_q &= Q(created_at__gte=datetime.combine(start_date, time.min))
        if end_date:
            report_q &= Q(created_at__lte=datetime.combine(end_date, time.max))
        reports = await WorkReport.filter(report_q).order_by("-created_at") if task_ids else []

        user_ids = {project.manager_id, project.creator_id}
        participant_map = await self.task_participant_map(task_ids)
        participant_user_ids = {user_id for user_ids in participant_map.values() for user_id in user_ids}
        user_ids.update(participant_user_ids)
        user_ids.update(task.assignee_id for task in tasks if task.assignee_id)
        user_ids.update(report.reporter_id for report in reports)
        user_map = {item.id: item for item in await User.filter(id__in=list(user_ids)).all()} if user_ids else {}

        project_data = await project.to_dict()
        manager = user_map.get(project.manager_id)
        project_data["manager_name"] = (manager.alias or manager.username) if manager else None

        task_data = []
        task_map = {task.id: task for task in tasks}
        for task in tasks:
            item = await task.to_dict()
            participant_ids = participant_map.get(task.id) or ([task.assignee_id] if task.assignee_id else [])
            participant_users = [user_map.get(user_id) for user_id in participant_ids]
            item["assignee_name"] = "、".join((user.alias or user.username) for user in participant_users if user) or None
            item["assignee_names"] = [(user.alias or user.username) for user in participant_users if user]
            item["assignee_ids"] = participant_ids
            task_data.append(item)

        report_data = []
        for report in reports[:20]:
            item = await report.to_dict()
            task = task_map.get(report.task_id)
            reporter = user_map.get(report.reporter_id)
            item["task_title"] = task.title if task else None
            item["reporter_name"] = (reporter.alias or reporter.username) if reporter else None
            report_data.append(item)

        return {
            "project": project,
            "tasks": tasks,
            "reports": reports,
            "project_data": project_data,
            "task_data": task_data,
            "report_data": report_data,
        }

    async def analyze_progress(self, state: ProjectWeeklyReportState) -> ProjectWeeklyReportState:
        tasks = state.get("task_data", [])
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            status = task.get("status")
            if status in status_counts:
                status_counts[status] += 1
        analysis = {
            "project_progress": state["project_data"].get("progress") or 0,
            "total_tasks": len(tasks),
            "status_counts": status_counts,
            "completed_tasks": [task for task in tasks if task.get("status") == TaskStatus.COMPLETED],
            "ongoing_tasks": [
                task
                for task in tasks
                if task.get("status") in [TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW, TaskStatus.NOT_STARTED]
            ],
            "blocked_tasks": [task for task in tasks if task.get("status") == TaskStatus.BLOCKED],
        }
        return {"analysis": analysis}

    async def analyze_risks(self, state: ProjectWeeklyReportState) -> ProjectWeeklyReportState:
        today = date.today()
        risks = []
        for task in state.get("task_data", []):
            due_date = self.parse_date(task.get("due_date"))
            is_overdue = due_date and due_date < today and task.get("status") not in [TaskStatus.COMPLETED, TaskStatus.ARCHIVED]
            if task.get("risk_level") in [RiskLevel.MEDIUM, RiskLevel.HIGH] or task.get("status") == TaskStatus.BLOCKED or is_overdue:
                risks.append({**task, "is_overdue": bool(is_overdue)})
        return {"risks": risks}

    async def summarize_reports(self, state: ProjectWeeklyReportState) -> ProjectWeeklyReportState:
        summaries = []
        for report in state.get("report_data", [])[:10]:
            task_title = report.get("task_title") or "未命名任务"
            reporter = report.get("reporter_name") or "未知成员"
            completed = "、".join(report.get("completed_items") or [])
            problems = "、".join(report.get("problems") or [])
            content = completed or report.get("raw_content") or "暂无详细内容"
            if problems:
                content = f"{content}；问题：{problems}"
            summaries.append(f"{reporter} 在《{task_title}》中汇报：{content}")
        return {"report_summaries": summaries}

    async def generate_report(self, state: ProjectWeeklyReportState) -> ProjectWeeklyReportState:
        prompt = self.build_prompt(state)
        if not settings.DEEPSEEK_API_KEY:
            result = self.fallback_report(state)
            return {"prompt": prompt, "raw_result": result.model_dump(mode="json")}

        try:
            data = await call_deepseek_json(
                system="你是 DriveMind 的项目周报 Agent。只能基于给定项目、任务、汇报证据生成周报，只输出符合 schema 的 JSON。",
                prompt=prompt,
            )
            return {"prompt": prompt, "raw_result": data}
        except AIServiceError:
            result = self.fallback_report(state)
            return {"prompt": prompt, "raw_result": result.model_dump(mode="json")}

    async def validate_result(self, state: ProjectWeeklyReportState) -> ProjectWeeklyReportState:
        result = ProjectWeeklyReportResult.model_validate(state["raw_result"])
        if not result.evidences:
            result.evidences = self.build_evidences(state)
        return {"result": result.model_dump(mode="json")}

    def build_prompt(self, state: ProjectWeeklyReportState) -> str:
        evidence = {
            "project": state.get("project_data", {}),
            "progress_analysis": state.get("analysis", {}),
            "risky_tasks": state.get("risks", []),
            "recent_reports_summary": state.get("report_summaries", []),
            "tasks": state.get("task_data", [])[:20],
            "reports": state.get("report_data", [])[:20],
        }
        return (
            "请生成一份面向项目经理的研发项目周报。进度数字必须使用证据中的 project_progress 和任务状态统计，"
            "不要虚构项目、任务、人员、日期。语言要适合企业研发运营管理场景，结论清晰，可直接放入 Word 文档。\n\n"
            f"统计周期：{self.period_text(state['req'])}\n"
            f"证据：{json.dumps(evidence, ensure_ascii=False, default=str)}\n\n"
            f"输出 JSON Schema：{json.dumps(ProjectWeeklyReportResult.model_json_schema(), ensure_ascii=False)}"
        )

    def fallback_report(self, state: ProjectWeeklyReportState) -> ProjectWeeklyReportResult:
        project = state.get("project_data", {})
        analysis = state.get("analysis", {})
        completed = analysis.get("completed_tasks", [])
        ongoing = analysis.get("ongoing_tasks", [])
        blocked = analysis.get("blocked_tasks", [])
        risks = state.get("risks", [])
        progress = analysis.get("project_progress", project.get("progress") or 0)
        total = analysis.get("total_tasks", 0)
        completed_count = len(completed)

        return ProjectWeeklyReportResult(
            title=f"{project.get('name', '项目')} 项目周报",
            project_name=project.get("name") or "未命名项目",
            project_code=project.get("code") or "",
            period=self.period_text(state["req"]),
            overall_summary=f"本周期项目整体进度为 {progress}%，共跟踪 {total} 个有效任务，已完成 {completed_count} 个任务。",
            progress_summary=f"项目当前可信进度为 {progress}%，该进度由任务状态和工作量加权计算得出。",
            completed_work=[self.task_line(task) for task in completed[:8]] or ["本周期暂无已完成任务记录。"],
            ongoing_tasks=[self.task_line(task) for task in ongoing[:8]] or ["当前暂无进行中任务记录。"],
            blocked_or_risky_items=[self.risk_line(task) for task in (risks or blocked)[:8]] or ["当前未发现明显阻塞或中高风险事项。"],
            recent_reports_summary=state.get("report_summaries", []) or ["本周期暂无员工工作汇报记录。"],
            next_week_plan=self.next_week_plan(ongoing, risks),
            management_suggestions=self.management_suggestions(progress, risks, blocked),
            evidences=self.build_evidences(state),
        )

    def next_week_plan(self, ongoing: list[dict], risks: list[dict]) -> list[str]:
        plans = [f"继续推进：{self.task_line(task)}" for task in ongoing[:5]]
        if risks:
            plans.append("优先处理风险和阻塞任务，明确负责人、解决动作和完成时间。")
        return plans or ["保持项目例会节奏，持续更新任务状态和工作汇报。"]

    def management_suggestions(self, progress: int, risks: list[dict], blocked: list[dict]) -> list[str]:
        suggestions = []
        if blocked:
            suggestions.append("建议项目经理优先协调阻塞任务所需资源，避免影响整体交付节奏。")
        if risks:
            suggestions.append("建议对中高风险任务建立跟踪清单，每日确认风险变化和解决进展。")
        if progress < 50:
            suggestions.append("项目进度仍处于前中期，应重点关注任务拆解完整性和关键路径排期。")
        suggestions.append("继续要求成员提交结构化工作汇报，便于 AI 周报和管理问答形成可信证据链。")
        return suggestions

    def build_evidences(self, state: ProjectWeeklyReportState) -> list[dict]:
        return [
            {"type": "project", "data": state.get("project_data", {})},
            *[{"type": "task", "data": item} for item in state.get("task_data", [])[:10]],
            *[{"type": "report", "data": item} for item in state.get("report_data", [])[:10]],
        ]

    def period_text(self, req: ProjectWeeklyReportRequest) -> str:
        start_date, end_date = self.resolve_period(req)
        return f"{start_date.isoformat()} 至 {end_date.isoformat()}"

    def resolve_period(self, req: ProjectWeeklyReportRequest) -> tuple[date, date]:
        end_date = req.end_date or date.today()
        start_date = req.start_date or (end_date - timedelta(days=6))
        return start_date, end_date

    def parse_date(self, value: Any) -> date | None:
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
        return None

    async def task_participant_map(self, task_ids: list[int]) -> dict[int, list[int]]:
        participants = await TaskParticipant.filter(task_id__in=task_ids).order_by("id") if task_ids else []
        result: dict[int, list[int]] = {}
        for participant in participants:
            result.setdefault(participant.task_id, []).append(participant.user_id)
        return result

    def task_line(self, task: dict) -> str:
        assignee = task.get("assignee_name") or "未分配"
        return f"{task.get('title') or '未命名任务'}（参与人：{assignee}，状态：{task.get('status')}，进度：{task.get('progress') or 0}%）"

    def risk_line(self, task: dict) -> str:
        text = self.task_line(task)
        if task.get("is_overdue"):
            text += "，已逾期"
        if task.get("risk_level"):
            text += f"，风险：{task.get('risk_level')}"
        return text


project_weekly_report_graph = ProjectWeeklyReportGraph()
