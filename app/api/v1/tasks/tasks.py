from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.task import task_controller
from app.core.dependency import DependAuth
from app.schemas import Success, SuccessExtra
from app.schemas.tasks import TaskBatchCreate, TaskCreate, TaskProgressUpdate, TaskUpdate

router = APIRouter()


@router.get("/list", summary="查看任务列表")
async def list_task(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    title: str = Query("", description="任务标题"),
    project_id: int = Query(None, description="项目ID"),
    assignee_id: int = Query(None, description="负责人ID"),
    status: str = Query("", description="任务状态"),
    risk_level: str = Query("", description="风险等级"),
    current_user=DependAuth,
):
    q = Q()
    if title:
        q &= Q(title__contains=title)
    if project_id is not None:
        q &= Q(project_id=project_id)
    if assignee_id is not None:
        q &= Q(assignee_id=assignee_id)
    if status:
        q &= Q(status=status)
    if risk_level:
        q &= Q(risk_level=risk_level)
    total, task_objs = await task_controller.list_visible(
        current_user=current_user, page=page, page_size=page_size, search=q, order=["due_date", "-updated_at"]
    )
    data = await task_controller.enrich_tasks(task_objs)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/my", summary="查看我的任务")
async def list_my_task(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    current_user=DependAuth,
):
    total, task_objs = await task_controller.list_visible(
        current_user=current_user,
        page=page,
        page_size=page_size,
        search=Q(assignee_id=current_user.id),
        order=["due_date", "-updated_at"],
    )
    data = await task_controller.enrich_tasks(task_objs)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看任务")
async def get_task(id: int = Query(..., description="任务ID"), current_user=DependAuth):
    task_obj = await task_controller.get_visible(id=id, current_user=current_user)
    return Success(data=await task_obj.to_dict())


@router.post("/create", summary="创建任务")
async def create_task(task_in: TaskCreate, current_user=DependAuth):
    await task_controller.create_task(obj_in=task_in, creator_id=current_user.id)
    return Success(msg="Created Successfully")


@router.post("/batch_create", summary="批量创建任务")
async def batch_create_task(task_in: TaskBatchCreate, current_user=DependAuth):
    await task_controller.batch_create_tasks(obj_in=task_in, creator_id=current_user.id)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新任务")
async def update_task(task_in: TaskUpdate, current_user=DependAuth):
    await task_controller.update_task(obj_in=task_in, current_user=current_user)
    return Success(msg="Updated Successfully")


@router.post("/progress", summary="更新任务进度")
async def update_task_progress(task_in: TaskProgressUpdate, current_user=DependAuth):
    await task_controller.update_progress(obj_in=task_in, current_user=current_user)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="归档任务")
async def delete_task(id: int = Query(..., description="任务ID"), current_user=DependAuth):
    await task_controller.archive_task(id=id, current_user=current_user)
    return Success(msg="Archived Successfully")
