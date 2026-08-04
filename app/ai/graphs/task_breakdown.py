import json

from langgraph.graph import END, StateGraph

from app.models.enums import RiskLevel, TaskPriority, TaskWorkload
from app.schemas.ai import TaskBreakdownItem, TaskBreakdownRequest, TaskBreakdownResult
from app.settings.config import settings

from .llm import call_deepseek_json
from .state import TaskBreakdownState


class TaskBreakdownGraph:
    def __init__(self):
        graph = StateGraph(TaskBreakdownState)
        graph.add_node("prepare_prompt", self.prepare_prompt)
        graph.add_node("call_model_or_fallback", self.call_model_or_fallback)
        graph.add_node("validate_result", self.validate_result)
        graph.set_entry_point("prepare_prompt")
        graph.add_edge("prepare_prompt", "call_model_or_fallback")
        graph.add_edge("call_model_or_fallback", "validate_result")
        graph.add_edge("validate_result", END)
        self.graph = graph.compile()

    async def run(self, req: TaskBreakdownRequest) -> TaskBreakdownResult:
        state = await self.graph.ainvoke({"req": req})
        return TaskBreakdownResult.model_validate(state["result"])

    async def prepare_prompt(self, state: TaskBreakdownState) -> TaskBreakdownState:
        req = state["req"]
        prompt = (
            "请把研发项目目标拆解成 4 到 8 个可执行任务。"
            "任务要适合企业研发运营管理平台演示，标题简短，描述清晰，优先级、工作量和风险要合理。"
            "工作量只允许 simple、normal、complex，分别代表简单、普通、复杂。\n\n"
            f"项目输入：{json.dumps(req.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            f"输出 JSON Schema：{json.dumps(TaskBreakdownResult.model_json_schema(), ensure_ascii=False)}"
        )
        return {"prompt": prompt}

    async def call_model_or_fallback(self, state: TaskBreakdownState) -> TaskBreakdownState:
        req = state["req"]
        if not settings.DEEPSEEK_API_KEY:
            result = self.fallback_breakdown(req)
            return {"raw_result": result.model_dump(mode="json")}

        data = await call_deepseek_json(
            system="你是 DriveMind 的任务拆解 Agent，只输出符合 schema 的 JSON，不直接修改数据库。",
            prompt=state["prompt"],
        )
        return {"raw_result": data}

    async def validate_result(self, state: TaskBreakdownState) -> TaskBreakdownState:
        result = TaskBreakdownResult.model_validate(state["raw_result"])
        return {"result": result.model_dump(mode="json")}

    def fallback_breakdown(self, req: TaskBreakdownRequest) -> TaskBreakdownResult:
        titles = [
            "需求梳理与范围确认",
            "系统设计与数据模型设计",
            "后端接口开发",
            "前端页面开发",
            "联调测试与上线准备",
        ]
        tasks = []
        for index, title in enumerate(titles):
            assignee_id = req.assignee_ids[index % len(req.assignee_ids)] if req.assignee_ids else None
            tasks.append(
                TaskBreakdownItem(
                    title=title,
                    desc=f"围绕“{req.goal}”完成{title}。",
                    assignee_id=assignee_id,
                    priority=TaskPriority.HIGH if index in [0, 2] else TaskPriority.MEDIUM,
                    workload=TaskWorkload.COMPLEX if index in [1, 2, 3] else TaskWorkload.NORMAL,
                    due_date=req.end_date,
                    risk_level=RiskLevel.MEDIUM if index == 4 else RiskLevel.LOW,
                )
            )
        return TaskBreakdownResult(tasks=tasks, summary="已按研发项目常见流程生成可编辑任务草案。")


task_breakdown_graph = TaskBreakdownGraph()
