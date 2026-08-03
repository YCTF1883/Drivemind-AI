from fastapi import APIRouter

from .tasks import router

tasks_router = APIRouter()
tasks_router.include_router(router, tags=["任务管理"])

__all__ = ["tasks_router"]
