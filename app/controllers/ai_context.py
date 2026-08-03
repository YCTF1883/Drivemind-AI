from datetime import datetime, timedelta

from app.models.admin import User
from app.models.business import AIConversationMessage
from app.schemas.ai import ManagerAnswerResult


class AIContextController:
    async def get_recent(self, session_id: str, user: User, limit: int) -> list[dict]:
        messages = (
            await AIConversationMessage.filter(session_id=session_id, user_id=user.id)
            .order_by("-created_at", "-id")
            .limit(limit)
        )
        messages = list(reversed(messages))
        return [
            {
                "role": message.role,
                "content": message.content,
                "metadata": message.metadata or {},
                "created_at": message.created_at,
            }
            for message in messages
        ]

    async def append_pair(
        self,
        session_id: str,
        user: User,
        question: str,
        answer: ManagerAnswerResult,
        query_id: int,
    ) -> None:
        await AIConversationMessage.create(
            session_id=session_id,
            user_id=user.id,
            role="user",
            content=question,
            metadata={"query_id": query_id},
        )
        await AIConversationMessage.create(
            session_id=session_id,
            user_id=user.id,
            role="assistant",
            content=answer.answer,
            metadata={"query_id": query_id, "evidences": answer.evidences},
        )

    async def trim_session(self, session_id: str, user: User, max_messages: int) -> int:
        messages = (
            await AIConversationMessage.filter(session_id=session_id, user_id=user.id)
            .order_by("-created_at", "-id")
            .offset(max_messages)
        )
        ids = [message.id for message in messages]
        if not ids:
            return 0
        return await AIConversationMessage.filter(id__in=ids).delete()

    async def cleanup_before(self, before_time: datetime) -> int:
        return await AIConversationMessage.filter(created_at__lt=before_time).delete()

    async def cleanup_expired(self, days: int) -> tuple[int, datetime]:
        before_time = datetime.now() - timedelta(days=days)
        deleted_count = await self.cleanup_before(before_time)
        return deleted_count, before_time


ai_context_controller = AIContextController()
