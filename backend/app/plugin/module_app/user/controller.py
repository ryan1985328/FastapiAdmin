from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import db_getter

from ..auth.dependencies import get_current_app_user
from .model import AppUserModel
from .schema import AppUserOutSchema, AppUserProfileUpdateSchema
from .service import AppUserService

AppUserRouter = APIRouter(prefix="/user", tags=["App用户"])


@AppUserRouter.get("/profile", summary="获取App用户资料", response_model=ResponseSchema[AppUserOutSchema])
async def get_app_user_profile_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserService(db).to_out(user)
    return SuccessResponse(data=result, msg="获取用户资料成功")


@AppUserRouter.put("/profile", summary="更新App用户资料", response_model=ResponseSchema[AppUserOutSchema])
async def update_app_user_profile_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    data: Annotated[AppUserProfileUpdateSchema, Body(description="App用户可编辑资料")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserService(db).update_profile(user, data)
    return SuccessResponse(data=result, msg="更新用户资料成功")


__all__ = ["AppUserRouter"]
