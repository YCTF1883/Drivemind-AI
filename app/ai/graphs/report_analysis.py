import json

from langgraph.graph import END, StateGraph

from app.controllers.progress import task_status_progress
from app.models.business import Task
from app.models.enums import RiskLevel, TaskStatus
from app.schemas.reports import ReportAnalysisResult
from app.settings.config import settings

from .llm import call_deepseek_json
from .state import ReportAnalysisState


class ReportAnalysisGraph:
    def __init__(self):
        graph = StateGraph(ReportAnalysisState)
        graph.add_node("prepare_task_context", self.prepare_task_context)
        graph.add_node("analyze_report_content", self.analyze_report_content)
        graph.add_node("apply_progress_policy", self.apply_progress_policy)
        graph.add_node("validate_result", self.validate_result)
        graph.set_entry_point("prepare_task_context")
        graph.add_edge("prepare_task_context", "analyze_report_content")
        graph.add_edge("analyze_report_content", "apply_progress_policy")
        graph.add_edge("apply_progress_policy", "validate_result")
        graph.add_edge("validate_result", END)
        self.graph = graph.compile()

    async def run(self, task: Task, content: str) -> ReportAnalysisResult:
        state = await self.graph.ainvoke({"task": task, "content": content})
        return ReportAnalysisResult.model_validate(state["result"])

    async def prepare_task_context(self, state: ReportAnalysisState) -> ReportAnalysisState:
        task = state["task"]
        task_data = await task.to_dict()
        prompt = (
            "请分析员工自然语言工作汇报，提取完成事项、问题、风险、所需支持、建议动作。"
            "任务进度由系统根据任务状态自动估算，不要机械生成固定百分比；"
            "progress_after 只填写当前任务状态对应的系统估算值，progress_delta 只填写与当前任务进度的非负差值。"
            "状态估算规则：not_started=0，blocked=30，in_progress=50，in_review=80，completed=100。\n\n"
            f"任务信息：{json.dumps(task_data, ensure_ascii=False)}\n"
            f"汇报原文：{state['content']}\n\n"
            f"输出 JSON Schema：{json.dumps(ReportAnalysisResult.model_json_schema(), ensure_ascii=False)}"
        )
        return {"task_data": task_data, "prompt": prompt}

    async def analyze_report_content(self, state: ReportAnalysisState) -> ReportAnalysisState:
        if not settings.DEEPSEEK_API_KEY:
            result = self.fallback_report(state["task"], state["content"])
            return {"raw_result": result.model_dump(mode="json")}

        data = await call_deepseek_json(
            system="你是 DriveMind 的汇报分析 Agent，只输出符合 schema 的 JSON，不能直接更新任务。",
            prompt=state["prompt"],
        )
        return {"raw_result": data}

    async def apply_progress_policy(self, state: ReportAnalysisState) -> ReportAnalysisState:
        task = state["task"]
        result = ReportAnalysisResult.model_validate(state["raw_result"])
        next_progress = task_status_progress(
            TaskStatus.BLOCKED
            if result.problems or result.support_needed or result.risk_level != RiskLevel.LOW
            else TaskStatus.IN_PROGRESS
        )
        result.progress_after = next_progress
        result.progress_delta = max(0, next_progress - task.progress)
        return {"raw_result": result.model_dump(mode="json")}

    async def validate_result(self, state: ReportAnalysisState) -> ReportAnalysisState:
        result = ReportAnalysisResult.model_validate(state["raw_result"])
        return {"result": result.model_dump(mode="json")}

    def fallback_report(self, task: Task, content: str) -> ReportAnalysisResult:
        problems = []
        support_needed = []
        risk_level = RiskLevel.LOW
        if any(keyword in content for keyword in ["问题", "失败", "阻塞", "不稳定", "延期", "风险"]):
            problems.append(content)
            risk_level = RiskLevel.MEDIUM
        if any(keyword in content for keyword in ["需要", "协助", "支持", "排查"]):
            support_needed.append("需要相关同事协助排查")
        next_status = TaskStatus.BLOCKED if problems or support_needed or risk_level != RiskLevel.LOW else TaskStatus.IN_PROGRESS
        progress_after = task_status_progress(next_status)
        return ReportAnalysisResult(
            completed_items=[content] if not problems else [],
            problems=problems,
            risk_level=risk_level,
            support_needed=support_needed,
            suggestions=["建议项目经理关注该任务进展" if risk_level != RiskLevel.LOW else "继续按计划推进"],
            progress_delta=max(0, progress_after - task.progress),
            progress_after=progress_after,
        )


report_analysis_graph = ReportAnalysisGraph()
