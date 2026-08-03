from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.report import report_controller
from app.core.dependency import DependAuth
from app.models.admin import User
from app.models.business import Project, Task
from app.schemas import Success, SuccessExtra
from app.schemas.reports import ReportCreate

router = APIRouter()


@router.get("/list", summary="查看汇报列表")
async def list_report(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    task_id: int = Query(None, description="任务ID"),
    reporter_id: int = Query(None, description="提交人ID"),
    keyword: str = Query("", description="项目、任务、提交人或汇报关键词"),
    risk_level: str = Query("", description="风险等级"),
    current_user=DependAuth,
):
    q = Q()
    if task_id is not None:
        q &= Q(task_id=task_id)
    if reporter_id is not None:
        q &= Q(reporter_id=reporter_id)
    if risk_level:
        q &= Q(risk_level=risk_level)
    if keyword:
        project_ids = await Project.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword)).values_list(
            "id", flat=True
        )
        task_ids = await Task.filter(Q(title__icontains=keyword) | Q(project_id__in=list(project_ids))).values_list(
            "id", flat=True
        )
        reporter_ids = await User.filter(Q(username__icontains=keyword) | Q(alias__icontains=keyword)).values_list(
            "id", flat=True
        )
        q &= (
            Q(raw_content__icontains=keyword)
            | Q(task_id__in=list(task_ids))
            | Q(reporter_id__in=list(reporter_ids))
        )
    total, report_objs = await report_controller.list_visible(
        current_user=current_user, page=page, page_size=page_size, search=q, order=["-created_at"]
    )
    data = await report_controller.enrich_reports(report_objs)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看汇报")
async def get_report(id: int = Query(..., description="汇报ID"), current_user=DependAuth):
    report_obj = await report_controller.get_visible(id=id, current_user=current_user)
    data = await report_controller.enrich_reports([report_obj])
    return Success(data=data[0] if data else {})


@router.post("/confirm", summary="确认提交汇报")
async def confirm_report(report_in: ReportCreate, current_user=DependAuth):
    await report_controller.confirm_report(obj_in=report_in, reporter=current_user)
    return Success(msg="Submitted Successfully")


@router.delete("/delete", summary="删除汇报")
async def delete_report(id: int = Query(..., description="汇报ID"), current_user=DependAuth):
    await report_controller.delete_report(id=id, current_user=current_user)
    return Success(msg="Deleted Successfully")
