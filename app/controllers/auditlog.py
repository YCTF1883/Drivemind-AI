from datetime import datetime, timedelta

from app.models.admin import AuditLog


class AuditLogController:
    async def cleanup_before(self, before_time: datetime) -> int:
        return await AuditLog.filter(created_at__lt=before_time).delete()

    async def cleanup_expired(self, days: int) -> tuple[int, datetime]:
        before_time = datetime.now() - timedelta(days=days)
        deleted_count = await self.cleanup_before(before_time)
        return deleted_count, before_time


audit_log_controller = AuditLogController()
