from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.project import project_controller
from app.core.dependency import DependAuth
from app.schemas import Success, SuccessExtra
from app.schemas.projects import ProjectCreate, ProjectUpdate

router = APIRouter()


@router.get("/list", summary="查看项目列表")
async def list_project(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="项目名称"),
    code: str = Query("", description="项目编码"),
    status: str = Query("", description="项目状态"),
    risk_level: str = Query("", description="风险等级"),
    current_user=DependAuth,
):
    q = Q()
    if name:
        q &= Q(name__contains=name)
    if code:
        q &= Q(code__contains=code)
    if status:
        q &= Q(status=status)
    if risk_level:
        q &= Q(risk_level=risk_level)
    total, project_objs = await project_controller.list_visible(
        current_user=current_user, page=page, page_size=page_size, search=q, order=["-updated_at"]
    )
    data = [await obj.to_dict() for obj in project_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看项目")
async def get_project(id: int = Query(..., description="项目ID"), current_user=DependAuth):
    project_obj = await project_controller.get_visible(id=id, current_user=current_user)
    return Success(data=await project_obj.to_dict())


@router.post("/create", summary="创建项目")
async def create_project(project_in: ProjectCreate, current_user=DependAuth):
    await project_controller.create_project(obj_in=project_in, creator_id=current_user.id)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新项目")
async def update_project(project_in: ProjectUpdate, current_user=DependAuth):
    await project_controller.update_project(obj_in=project_in, current_user=current_user)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="归档项目")
async def delete_project(id: int = Query(..., description="项目ID"), current_user=DependAuth):
    await project_controller.archive_project(id=id, current_user=current_user)
    return Success(msg="Archived Successfully")
