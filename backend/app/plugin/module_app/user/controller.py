from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.common.response import ResponseSchema, SuccessResponse

from ..auth.dependencies import get_current_app_user
from .model import AppUserModel
from .schema import AppUserOutSchema

AppUserRouter = APIRouter(prefix="/user", tags=["App用户"])


@AppUserRouter.get("/profile", summary="获取App用户资料", response_model=ResponseSchema[AppUserOutSchema])
async def get_app_user_profile_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
) -> JSONResponse:
    return SuccessResponse(data=AppUserOutSchema.model_validate(user), msg="获取用户资料成功")


__all__ = ["AppUserRouter"]
