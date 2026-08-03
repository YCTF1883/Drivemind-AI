from fastapi import APIRouter

from .reports import router

reports_router = APIRouter()
reports_router.include_router(router, tags=["工作汇报"])

__all__ = ["reports_router"]
