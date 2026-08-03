from fastapi import APIRouter

from .dashboard import router

dashboard_router = APIRouter()
dashboard_router.include_router(router, tags=["工作台"])

__all__ = ["dashboard_router"]
