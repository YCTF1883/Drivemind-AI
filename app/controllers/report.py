from fastapi import HTTPException
from tortoise.expressions import Q
from tortoise.transactions import atomic

from app.controllers.business_access import is_business_manager
from app.controllers.progress import task_status_progress
from app.core.crud import CRUDBase
from app.models.admin import User
from app.models.business import Project, Task, WorkReport
from app.models.enums import TaskStatus
from app.schemas.reports import ReportCreate


class ReportController(CRUDBase[WorkReport, ReportCreate, ReportCreate]):
    def __init__(self):
        super().__init__(model=WorkReport)

    async def enrich_reports(self, reports: list[WorkReport]) -> list[dict]:
        task_ids = {report.task_id for report in reports}
        tasks = await Task.filter(id__in=list(task_ids)).all() if task_ids else []
        task_map = {task.id: task for task in tasks}

        project_ids = {task.project_id for task in tasks}
        projects = await Project.filter(id__in=list(project_ids)).all() if project_ids else []
        project_map = {project.id: project for project in projects}

        user_ids = {report.reporter_id for report in reports}
        user_ids.update(task.assignee_id for task in tasks if task.assignee_id)
        users = await User.filter(id__in=list(user_ids)).all() if user_ids else []
        user_map = {user.id: user for user in users}

        data = []
        for report in reports:
            item = await report.to_dict()
            task = task_map.get(report.task_id)
            project = project_map.get(task.project_id) if task else None
            reporter = user_map.get(report.reporter_id)
            assignee = user_map.get(task.assignee_id) if task and task.assignee_id else None

            reporter_name = (reporter.alias or reporter.username) if reporter else None
            assignee_name = (assignee.alias or assignee.username) if assignee else None

            item.update(
                {
                    "task_title": task.title if task else None,
                    "task_status": task.status.value if task else None,
                    "task_progress": task.progress if task else None,
                    "task_assignee_id": task.assignee_id if task else None,
                    "assignee_name": assignee_name,
                    "assignee_username": assignee.username if assignee else None,
                    "project_id": project.id if project else None,
                    "project_name": project.name if project else None,
                    "project_code": project.code if project else None,
                    "reporter_name": reporter_name,
                    "reporter_username": reporter.username if reporter else None,
                }
            )
            data.append(item)
        return data

    async def list_visible(self, current_user: User, page: int, page_size: int, search: Q = Q(), order: list = []):
        if await is_business_manager(current_user):
            q = search
        else:
            from app.models.business import Task

            visible_tasks = await Task.filter(
                Q(is_archived=False) & (Q(assignee_id=current_user.id) | Q(creator_id=current_user.id))
            ).values_list("id", flat=True)
            q = Q(reporter_id=current_user.id) | Q(task_id__in=list(visible_tasks))
            q &= search
        return await self.list(page=page, page_size=page_size, search=q, order=order)

    async def get_visible(self, id: int, current_user: User) -> WorkReport:
        report = await self.get(id=id)
        if await is_business_manager(current_user) or report.reporter_id == current_user.id:
            return report
        from app.controllers.task import task_controller

        await task_controller.get_visible(report.task_id, current_user)
        return report

    @atomic()
    async def confirm_report(self, obj_in: ReportCreate, reporter: User) -> WorkReport:
        from app.controllers.task import task_controller
        from app.models.business import Task

        task = await task_controller.get_visible(obj_in.task_id, reporter)
        if not reporter.is_superuser and task.assignee_id != reporter.id:
            raise HTTPException(status_code=403, detail="Only task assignee can submit report")

        next_status = obj_in.task_status
        if next_status is None:
            if obj_in.problems or obj_in.support_needed or obj_in.risk_level.value in ["medium", "high"]:
                next_status = TaskStatus.BLOCKED
            else:
                next_status = TaskStatus.IN_PROGRESS
        next_progress = task_status_progress(next_status)

        data = obj_in.model_dump(exclude={"task_status"})
        data["reporter_id"] = reporter.id
        data["progress_after"] = next_progress
        data["progress_delta"] = max(0, next_progress - task.progress)
        report = await self.create(data)

        update_fields = {
            "progress": next_progress,
            "risk_level": obj_in.risk_level,
            "status": next_status,
        }
        await Task.filter(id=task.id).update(**update_fields)
        await task_controller._recalculate_project(task.project_id)
        return report
    async def delete_report(self, id: int, current_user: User) -> None:
        report = await self.get_visible(id=id, current_user=current_user)
        if not await is_business_manager(current_user) and report.reporter_id != current_user.id:
            raise HTTPException(status_code=403, detail="No permission to delete this report")
        await self.remove(id=id)


report_controller = ReportController()
