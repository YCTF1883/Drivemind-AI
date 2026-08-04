from fastapi import HTTPException
from tortoise.expressions import Q

from app.controllers.business_access import is_business_manager
from app.controllers.progress import task_status_progress, task_workload_value
from app.core.crud import CRUDBase
from app.models.admin import User
from app.models.business import Project, Task
from app.models.enums import ProjectStatus, RiskLevel, TaskStatus
from app.schemas.projects import ProjectCreate, ProjectUpdate


class ProjectController(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self):
        super().__init__(model=Project)

    async def visible_query(self, current_user: User) -> Q:
        q = Q(is_deleted=False)
        if await is_business_manager(current_user):
            return q
        task_project_ids = await Task.filter(assignee_id=current_user.id, is_archived=False).values_list("project_id", flat=True)
        return q & (
            Q(manager_id=current_user.id) | Q(creator_id=current_user.id) | Q(id__in=list(task_project_ids))
        )

    async def list_visible(self, current_user: User, page: int, page_size: int, search: Q = Q(), order: list = []):
        return await self.list(page=page, page_size=page_size, search=await self.visible_query(current_user) & search, order=order)

    async def get_visible(self, id: int, current_user: User) -> Project:
        project = await self.get(id=id)
        if project.is_deleted:
            raise HTTPException(status_code=404, detail="Project not found")
        if await is_business_manager(current_user) or project.manager_id == current_user.id or project.creator_id == current_user.id:
            return project
        task = await Task.filter(project_id=id, assignee_id=current_user.id).first()
        if task:
            return project
        raise HTTPException(status_code=403, detail="No permission for this project")

    async def _ensure_active_unique(self, name: str, code: str, exclude_id: int | None = None):
        q = Q(is_deleted=False) & (Q(name=name) | Q(code=code))
        if exclude_id is not None:
            q &= ~Q(id=exclude_id)
        existing = await Project.filter(q).first()
        if not existing:
            return
        if existing.code == code:
            raise HTTPException(status_code=400, detail="项目编码已存在")
        raise HTTPException(status_code=400, detail="项目名称已存在")

    async def create_project(self, obj_in: ProjectCreate, creator_id: int) -> Project:
        await self._ensure_active_unique(name=obj_in.name, code=obj_in.code)
        data = obj_in.model_dump()
        data["creator_id"] = creator_id
        return await self.create(data)

    async def update_project(self, obj_in: ProjectUpdate, current_user: User) -> Project:
        project = await self.get_visible(obj_in.id, current_user)
        if not await is_business_manager(current_user) and project.manager_id != current_user.id and project.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="No permission to update this project")
        await self._ensure_active_unique(name=obj_in.name, code=obj_in.code, exclude_id=obj_in.id)
        return await self.update(id=obj_in.id, obj_in=obj_in)

    async def archive_project(self, id: int, current_user: User) -> None:
        project = await self.get_visible(id, current_user)
        if not await is_business_manager(current_user) and project.manager_id != current_user.id and project.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="No permission to archive this project")
        project.status = ProjectStatus.ARCHIVED
        project.is_deleted = True
        await project.save()
        await Task.filter(project_id=project.id, is_archived=False).update(status=TaskStatus.ARCHIVED, is_archived=True)

    async def recalculate_progress(self, project_id: int):
        project = await self.get(id=project_id)
        tasks = await Task.filter(project_id=project_id, is_archived=False)
        if not tasks:
            project.progress = 0
            project.risk_level = RiskLevel.LOW
            await project.save()
            return project

        total_weight = sum(task_workload_value(task.workload) for task in tasks)
        weighted_progress = sum(
            task_workload_value(task.workload) * task_status_progress(task.status)
            for task in tasks
        )
        project.progress = round(weighted_progress / total_weight) if total_weight else 0
        risk_values = [task.risk_level for task in tasks]
        if RiskLevel.HIGH in risk_values:
            project.risk_level = RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_values:
            project.risk_level = RiskLevel.MEDIUM
        else:
            project.risk_level = RiskLevel.LOW
        if all(task.status == TaskStatus.COMPLETED for task in tasks):
            project.status = ProjectStatus.COMPLETED
        elif project.status == ProjectStatus.COMPLETED:
            project.status = ProjectStatus.ACTIVE
        await project.save()
        return project


project_controller = ProjectController()
