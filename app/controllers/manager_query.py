from fastapi import HTTPException
from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.admin import User
from app.models.business import ManagerQuery
from app.schemas.ai import ManagerAnswerResult, ManagerQuestionRequest


class ManagerQueryController(CRUDBase[ManagerQuery, ManagerQuestionRequest, ManagerQuestionRequest]):
    def __init__(self):
        super().__init__(model=ManagerQuery)

    async def create_query(self, question: str, result: ManagerAnswerResult, user: User) -> ManagerQuery:
        return await self.create(
            {
                "question": question,
                "answer": result.answer,
                "evidences": result.evidences,
                "user_id": user.id,
            }
        )

    async def list_visible(self, user: User, page: int, page_size: int):
        if user.is_superuser:
            return await self.list(page=page, page_size=page_size, order=["-created_at"])
        return await self.list(page=page, page_size=page_size, search=Q(user_id=user.id), order=["-created_at"])

    async def delete_visible(self, id: int, user: User) -> None:
        query = await self.model.get_or_none(id=id)
        if not query:
            raise HTTPException(status_code=404, detail="Manager query not found")
        if not user.is_superuser and query.user_id != user.id:
            raise HTTPException(status_code=403, detail="No permission to delete this manager query")
        await query.delete()


manager_query_controller = ManagerQueryController()
