from fastapi import APIRouter, HTTPException, Query

from app.ai import ai_workflow
from app.ai.exceptions import AIServiceError
from app.controllers.ai_context import ai_context_controller
from app.controllers.manager_query import manager_query_controller
from app.controllers.task import task_controller
from app.core.dependency import DependAuth
from app.schemas import Success, SuccessExtra
from app.schemas.ai import ManagerQuestionRequest, TaskBreakdownRequest
from app.schemas.reports import ReportAnalyzeRequest
from app.settings.config import settings

router = APIRouter()


@router.post("/task_breakdown", summary="AI 拆解任务")
async def task_breakdown(req: TaskBreakdownRequest, current_user=DependAuth):
    if req.project_id is not None:
        await task_controller._ensure_project_editable(req.project_id, current_user.id)
    try:
        result = await ai_workflow.breakdown_tasks(req)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Success(data=result.model_dump(mode="json"))


@router.post("/report_analyze", summary="AI 分析工作汇报")
async def report_analyze(req: ReportAnalyzeRequest, current_user=DependAuth):
    task = await task_controller.get_visible(id=req.task_id, current_user=current_user)
    try:
        result = await ai_workflow.analyze_report(task, req.content)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Success(data=result.model_dump(mode="json"))


@router.post("/manager_question", summary="管理者 AI 问答")
async def manager_question(req: ManagerQuestionRequest, current_user=DependAuth):
    session_id = req.session_id or f"manager:{current_user.id}"
    context_messages = await ai_context_controller.get_recent(
        session_id=session_id,
        user=current_user,
        limit=settings.AI_CONTEXT_RECENT_MESSAGES,
    )
    try:
        result = await ai_workflow.answer_manager_question(current_user, req.question, context_messages=context_messages)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    query = await manager_query_controller.create_query(req.question, result, current_user)
    await ai_context_controller.append_pair(session_id, current_user, req.question, result, query.id)
    await ai_context_controller.trim_session(session_id, current_user, settings.AI_CONTEXT_MAX_MESSAGES_PER_SESSION)
    data = result.model_dump(mode="json")
    data["id"] = query.id
    return Success(data=data)


@router.get("/manager_history", summary="查看管理问答历史")
async def manager_history(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    current_user=DependAuth,
):
    total, query_objs = await manager_query_controller.list_visible(user=current_user, page=page, page_size=page_size)
    data = [await obj.to_dict() for obj in query_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.delete("/manager_history", summary="删除管理问答历史")
async def delete_manager_history(id: int = Query(..., description="问答历史ID"), current_user=DependAuth):
    await manager_query_controller.delete_visible(id=id, user=current_user)
    return Success(msg="Deleted Successfully")
