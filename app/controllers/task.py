from fastapi import HTTPException
from tortoise.expressions import Q
from tortoise.transactions import atomic

from app.controllers.business_access import is_business_manager
from app.core.crud import CRUDBase
from app.models.admin import User
from app.models.business import Project, Task, WorkReport
from app.models.enums import TaskSource, TaskStatus
from app.schemas.tasks import TaskBatchCreate, TaskCreate, TaskProgressUpdate, TaskUpdate


class TaskController(CRUDBase[Task, TaskCreate, TaskUpdate]):
    def __init__(self):
        super().__init__(model=Task)

    async def enrich_tasks(self, tasks: list[Task]) -> list[dict]:
        task_ids = [task.id for task in tasks]
        reports = await WorkReport.filter(task_id__in=task_ids).order_by("-created_at") if task_ids else []

        latest_report_map = {}
        reporter_ids = set()
        for report in reports:
            if report.task_id not in latest_report_map:
                latest_report_map[report.task_id] = report
                reporter_ids.add(report.reporter_id)

        reporters = await User.filter(id__in=list(reporter_ids)).all() if reporter_ids else []
        reporter_map = {reporter.id: reporter for reporter in reporters}

        data = []
        for task in tasks:
            item = await task.to_dict()
            latest_report = latest_report_map.get(task.id)
            reporter = reporter_map.get(latest_report.reporter_id) if latest_report else None
            reporter_name = (reporter.alias or reporter.username) if reporter else None

            item.update(
                {
                    "latest_report_id": latest_report.id if latest_report else None,
                    "latest_report_content": latest_report.raw_content if latest_report else None,
                    "latest_report_time": latest_report.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_report else None,
                    "latest_reporter_id": latest_report.reporter_id if latest_report else None,
                    "latest_reporter_name": reporter_name,
                    "latest_reporter_username": reporter.username if reporter else None,
                    "latest_report_problems": latest_report.problems if latest_report else [],
                    "latest_report_support_needed": latest_report.support_needed if latest_report else [],
                    "latest_report_suggestions": latest_report.suggestions if latest_report else [],
                    "latest_report_risk_level": latest_report.risk_level.value if latest_report else None,
                    "latest_report_progress_after": latest_report.progress_after if latest_report else None,
                }
            )
            data.append(item)
        return data

    async def visible_query(self, current_user: User) -> Q:
        q = Q(is_archived=False)
        if await is_business_manager(current_user):
            return q
        return q & (Q(assignee_id=current_user.id) | Q(creator_id=current_user.id))

    async def list_visible(self, current_user: User, page: int, page_size: int, search: Q = Q(), order: list = []):
        if await is_business_manager(current_user):
            q = Q(is_archived=False) & search
        else:
            q = Q(is_archived=False) & (Q(assignee_id=current_user.id) | Q(creator_id=current_user.id)) & search
        return await self.list(page=page, page_size=page_size, search=q, order=order)

    async def get_visible(self, id: int, current_user: User) -> Task:
        task = await self.get(id=id)
        if task.is_archived:
            raise HTTPException(status_code=404, detail="Task not found")
        if await is_business_manager(current_user) or task.assignee_id == current_user.id or task.creator_id == current_user.id:
            return task
        project = await Project.filter(id=task.project_id, is_deleted=False).first()
        if project and (project.manager_id == current_user.id or project.creator_id == current_user.id):
            return task
        raise HTTPException(status_code=403, detail="No permission for this task")

    async def create_task(self, obj_in: TaskCreate, creator_id: int) -> Task:
        await self._ensure_project_editable(obj_in.project_id, creator_id)
        data = obj_in.model_dump()
        data["creator_id"] = creator_id
        task = await self.create(data)
        await self._recalculate_project(task.project_id)
        return task

    @atomic()
    async def batch_create_tasks(self, obj_in: TaskBatchCreate, creator_id: int) -> list[Task]:
        tasks = []
        for item in obj_in.tasks:
            await self._ensure_project_editable(item.project_id, creator_id)
            data = item.model_dump()
            data["creator_id"] = creator_id
            data["source"] = TaskSource.AI
            task = await self.create(data)
            tasks.append(task)
        project_ids = set(task.project_id for task in tasks)
        for project_id in project_ids:
            await self._recalculate_project(project_id)
        return tasks

    async def update_task(self, obj_in: TaskUpdate, current_user: User) -> Task:
        task = await self.get_visible(obj_in.id, current_user)
        if not await self._can_edit_task(task, current_user):
            raise HTTPException(status_code=403, detail="No permission to update this task")
        updated = await self.update(id=obj_in.id, obj_in=obj_in)
        await self._recalculate_project(updated.project_id)
        return updated

    async def update_progress(self, obj_in: TaskProgressUpdate, current_user: User) -> Task:
        task = await self.get_visible(obj_in.id, current_user)
        if not current_user.is_superuser and task.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assignee can update progress")
        if obj_in.progress < task.progress:
            raise HTTPException(status_code=400, detail="Progress cannot go backwards")
        if obj_in.status == TaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Assignee can only submit task for review, manager confirms completion")
        task.status = TaskStatus.IN_REVIEW if obj_in.progress >= 100 else obj_in.status
        task.progress = obj_in.progress
        task.risk_level = obj_in.risk_level
        await task.save()
        await self._recalculate_project(task.project_id)
        return task

    async def archive_task(self, id: int, current_user: User) -> None:
        task = await self.get_visible(id, current_user)
        if not await self._can_edit_task(task, current_user):
            raise HTTPException(status_code=403, detail="No permission to archive this task")
        task.status = TaskStatus.ARCHIVED
        task.is_archived = True
        await task.save()
        await self._recalculate_project(task.project_id)

    async def _ensure_project_editable(self, project_id: int, user_id: int):
        project = await Project.filter(id=project_id, is_deleted=False).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.manager_id != user_id and project.creator_id != user_id:
            user = await User.filter(id=user_id).first()
            if not user or not await is_business_manager(user):
                raise HTTPException(status_code=403, detail="No permission to create task in this project")

    async def _can_edit_task(self, task: Task, current_user: User) -> bool:
        if await is_business_manager(current_user) or task.creator_id == current_user.id:
            return True
        project = await Project.filter(id=task.project_id, is_deleted=False).first()
        return bool(project and (project.manager_id == current_user.id or project.creator_id == current_user.id))

    async def _recalculate_project(self, project_id: int):
        from app.controllers.project import project_controller

        await project_controller.recalculate_progress(project_id)


task_controller = TaskController()
