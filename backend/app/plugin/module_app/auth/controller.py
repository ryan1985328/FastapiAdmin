from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import JWTOutSchema
from app.core.dependencies import db_getter, redis_getter

from ..user.model import AppUserModel
from ..user.schema import AppLoginOutSchema, AppLoginSchema, AppRefreshTokenSchema, AppUserCreateSchema, AppUserOutSchema
from ..user.service import AppUserService
from .dependencies import AppOAuth2Schema, get_current_app_user
from .service import AppAuthService

AppAuthRouter = APIRouter(prefix="/auth", tags=["App用户认证"])


@AppAuthRouter.post("/register", summary="App用户注册", response_model=ResponseSchema[AppUserOutSchema])
async def register_app_user_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    data: Annotated[AppUserCreateSchema, Body(description="App用户注册参数")],
) -> JSONResponse:
    result = await AppUserService(db).register(data)
    return SuccessResponse(data=result, msg="注册成功")


@AppAuthRouter.post("/login", summary="App用户登录", response_model=ResponseSchema[AppLoginOutSchema])
async def login_app_user_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    redis: Annotated[Redis, Depends(redis_getter)],
    data: Annotated[AppLoginSchema, Body(description="App用户登录参数")],
) -> JSONResponse:
    result = await AppAuthService.login(db=db, redis=redis, data=data)
    return SuccessResponse(data=result, msg="登录成功")


@AppAuthRouter.post("/refresh", summary="刷新App用户令牌", response_model=ResponseSchema[JWTOutSchema])
async def refresh_app_user_token_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    redis: Annotated[Redis, Depends(redis_getter)],
    data: Annotated[AppRefreshTokenSchema, Body(description="刷新令牌参数")],
) -> JSONResponse:
    result = await AppAuthService.refresh_token(db=db, redis=redis, data=data)
    return SuccessResponse(data=result, msg="刷新成功")


@AppAuthRouter.get("/me", summary="获取当前App用户", response_model=ResponseSchema[AppUserOutSchema])
async def get_current_app_user_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserService(db).to_out(user)
    return SuccessResponse(data=result, msg="获取当前用户信息成功")


@AppAuthRouter.post("/logout", summary="App用户退出登录", response_model=ResponseSchema[None])
async def logout_app_user_controller(
    redis: Annotated[Redis, Depends(redis_getter)],
    _user: Annotated[AppUserModel, Depends(get_current_app_user)],
    token: Annotated[str, Depends(AppOAuth2Schema)],
) -> JSONResponse:
    await AppAuthService.logout(redis=redis, token=token)
    return SuccessResponse(msg="退出成功")


__all__ = ["AppAuthRouter"]
