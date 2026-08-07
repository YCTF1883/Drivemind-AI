from datetime import datetime, timedelta

from tortoise.expressions import Q

from app.controllers.business_access import is_business_manager
from app.models.admin import User
from app.models.business import Project, Task, TaskParticipant, WorkReport
from app.models.enums import ProjectStatus, RiskLevel, TaskStatus


class DashboardController:
    async def get_summary(self, current_user: User) -> dict:
        project_q, task_q = await self._build_visible_queries(current_user)
        visible_task_ids = list(await Task.filter(task_q).values_list("id", flat=True))
        report_q = Q(task_id__in=visible_task_ids) if visible_task_ids else Q(id__in=[])
        recent_days = datetime.now() - timedelta(days=7)

        project_total = await Project.filter(project_q).count()
        active_projects = await Project.filter(project_q & Q(status=ProjectStatus.ACTIVE)).count()
        task_total = await Task.filter(task_q).count()
        active_tasks = await Task.filter(task_q & Q(status=TaskStatus.IN_PROGRESS)).count()
        review_tasks = await Task.filter(task_q & Q(status=TaskStatus.IN_REVIEW)).count()
        blocked_tasks = await Task.filter(task_q & Q(status=TaskStatus.BLOCKED)).count()
        risk_tasks = await Task.filter(task_q & Q(risk_level=RiskLevel.HIGH)).count()
        weekly_reports = await WorkReport.filter(report_q & Q(created_at__gte=recent_days)).count()

        task_status_distribution = [
            {"status": status.value, "count": await Task.filter(task_q & Q(status=status)).count()} for status in TaskStatus
        ]
        risk_distribution = [
            {"risk_level": risk.value, "count": await Task.filter(task_q & Q(risk_level=risk)).count()} for risk in RiskLevel
        ]

        project_progress_objs = await Project.filter(project_q).order_by("risk_level", "progress", "-updated_at").limit(6)
        action_task_objs = await Task.filter(
            task_q & (Q(status__in=[TaskStatus.IN_REVIEW, TaskStatus.BLOCKED]) | Q(risk_level=RiskLevel.HIGH))
        ).order_by("due_date", "-updated_at").limit(6)
        recent_report_objs = await WorkReport.filter(report_q).order_by("-created_at").limit(5)

        return {
            "summary": {
                "project_total": project_total,
                "active_projects": active_projects,
                "task_total": task_total,
                "active_tasks": active_tasks,
                "review_tasks": review_tasks,
                "blocked_tasks": blocked_tasks,
                "risk_tasks": risk_tasks,
                "weekly_reports": weekly_reports,
            },
            "task_status_distribution": task_status_distribution,
            "risk_distribution": risk_distribution,
            "project_progress": [await self._project_item(project) for project in project_progress_objs],
            "action_items": [await self._task_action_item(task) for task in action_task_objs],
            "recent_reports": await self._report_items(list(recent_report_objs)),
        }

    async def _build_visible_queries(self, current_user: User) -> tuple[Q, Q]:
        project_q = Q(is_deleted=False)
        task_q = Q(is_archived=False)
        if await is_business_manager(current_user):
            return project_q, task_q

        managed_project_ids = list(
            await Project.filter(
                project_q & (Q(manager_id=current_user.id) | Q(creator_id=current_user.id))
            ).values_list("id", flat=True)
        )
        assigned_project_ids = list(
            await Task.filter(Q(is_archived=False) & Q(assignee_id=current_user.id)).values_list("project_id", flat=True)
        )
        participant_task_ids = list(await TaskParticipant.filter(user_id=current_user.id).values_list("task_id", flat=True))
        participant_project_ids = list(
            await Task.filter(Q(is_archived=False) & Q(id__in=participant_task_ids)).values_list("project_id", flat=True)
        ) if participant_task_ids else []
        visible_project_ids = list(set(managed_project_ids + assigned_project_ids + participant_project_ids))

        task_q &= (
            Q(assignee_id=current_user.id)
            | Q(creator_id=current_user.id)
            | Q(id__in=participant_task_ids)
            | Q(project_id__in=managed_project_ids)
        )
        project_q &= Q(id__in=visible_project_ids) | Q(manager_id=current_user.id) | Q(creator_id=current_user.id)
        return project_q, task_q

    async def _project_item(self, project: Project) -> dict:
        return {
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "status": project.status.value,
            "risk_level": project.risk_level.value,
            "progress": project.progress,
            "updated_at": project.updated_at.strftime("%Y-%m-%d %H:%M:%S") if project.updated_at else None,
        }

    async def _task_action_item(self, task: Task) -> dict:
        project = await Project.filter(id=task.project_id, is_deleted=False).first()
        participant_ids = list(
            await TaskParticipant.filter(task_id=task.id).order_by("id").values_list("user_id", flat=True)
        )
        if not participant_ids and task.assignee_id:
            participant_ids = [task.assignee_id]
        users = await User.filter(id__in=participant_ids).all() if participant_ids else []
        user_map = {user.id: user for user in users}
        assignee_names = [
            (user_map[user_id].alias or user_map[user_id].username) for user_id in participant_ids if user_id in user_map
        ]
        return {
            "id": task.id,
            "title": task.title,
            "project_name": project.name if project else None,
            "assignee_name": "、".join(assignee_names) if assignee_names else None,
            "status": task.status.value,
            "risk_level": task.risk_level.value,
            "progress": task.progress,
            "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
        }

    async def _report_items(self, reports: list[WorkReport]) -> list[dict]:
        task_ids = {report.task_id for report in reports}
        tasks = await Task.filter(id__in=list(task_ids)).all() if task_ids else []
        task_map = {task.id: task for task in tasks}

        project_ids = {task.project_id for task in tasks}
        projects = await Project.filter(id__in=list(project_ids)).all() if project_ids else []
        project_map = {project.id: project for project in projects}

        reporter_ids = {report.reporter_id for report in reports}
        reporters = await User.filter(id__in=list(reporter_ids)).all() if reporter_ids else []
        reporter_map = {reporter.id: reporter for reporter in reporters}

        data = []
        for report in reports:
            task = task_map.get(report.task_id)
            project = project_map.get(task.project_id) if task else None
            reporter = reporter_map.get(report.reporter_id)
            data.append(
                {
                    "id": report.id,
                    "task_title": task.title if task else None,
                    "project_name": project.name if project else None,
                    "reporter_name": (reporter.alias or reporter.username) if reporter else None,
                    "raw_content": report.raw_content,
                    "risk_level": report.risk_level.value,
                    "progress_after": report.progress_after,
                    "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else None,
                }
            )
        return data


dashboard_controller = DashboardController()
