from app.ai.graphs import manager_qa_graph, report_analysis_graph, task_breakdown_graph
from app.models.admin import User
from app.models.business import Task
from app.schemas.ai import ManagerAnswerResult, TaskBreakdownRequest, TaskBreakdownResult
from app.schemas.reports import ReportAnalysisResult


class DriveMindAIWorkflow:
    async def breakdown_tasks(self, req: TaskBreakdownRequest) -> TaskBreakdownResult:
        return await task_breakdown_graph.run(req)

    async def analyze_report(self, task: Task, content: str) -> ReportAnalysisResult:
        return await report_analysis_graph.run(task, content)

    async def answer_manager_question(
        self,
        user: User,
        question: str,
        context_messages: list[dict] | None = None,
    ) -> ManagerAnswerResult:
        return await manager_qa_graph.run(user, question, context_messages=context_messages or [])


ai_workflow = DriveMindAIWorkflow()
