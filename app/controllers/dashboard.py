from tortoise.expressions import Q

from app.models.admin import User
from app.models.business import Project, Task, WorkReport
from app.models.enums import RiskLevel, TaskStatus


class DashboardController:
    async def get_summary(self, current_user: User) -> dict:
        project_q = Q(is_deleted=False)
        task_q = Q(is_archived=False)
        if not current_user.is_superuser:
            managed_project_ids = await Project.filter(
                project_q & (Q(manager_id=current_user.id) | Q(creator_id=current_user.id))
            ).values_list("id", flat=True)
            task_q &= Q(assignee_id=current_user.id) | Q(creator_id=current_user.id) | Q(project_id__in=list(managed_project_ids))
            project_q &= Q(manager_id=current_user.id) | Q(creator_id=current_user.id) | Q(id__in=list(managed_project_ids))

        project_total = await Project.filter(project_q).count()
        active_tasks = await Task.filter(task_q & Q(status=TaskStatus.IN_PROGRESS)).count()
        risk_tasks = await Task.filter(task_q & Q(risk_level__in=[RiskLevel.MEDIUM, RiskLevel.HIGH])).count()
        visible_task_ids = await Task.filter(task_q).values_list("id", flat=True)
        pending_reports = await WorkReport.filter(
            Q(task_id__in=list(visible_task_ids)) & Q(risk_level__in=[RiskLevel.MEDIUM, RiskLevel.HIGH])
        ).count()
        recent_risks = await Task.filter(task_q & Q(risk_level__in=[RiskLevel.MEDIUM, RiskLevel.HIGH])).order_by(
            "-updated_at"
        ).limit(5)
        my_tasks = await Task.filter(task_q).order_by("due_date", "-updated_at").limit(5)

        return {
            "project_total": project_total,
            "active_tasks": active_tasks,
            "risk_tasks": risk_tasks,
            "pending_reports": pending_reports,
            "recent_risks": [await task.to_dict() for task in recent_risks],
            "my_tasks": [await task.to_dict() for task in my_tasks],
        }


dashboard_controller = DashboardController()
