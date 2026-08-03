from fastapi import APIRouter

from app.controllers.dashboard import dashboard_controller
from app.core.dependency import DependAuth
from app.schemas import Success

router = APIRouter()


@router.get("/summary", summary="查看工作台统计")
async def dashboard_summary(current_user=DependAuth):
    data = await dashboard_controller.get_summary(current_user=current_user)
    return Success(data=data)
