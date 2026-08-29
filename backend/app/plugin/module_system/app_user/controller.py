# -*- coding: utf-8 -*-

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import AppUserOutSchema, AppUserQueryParam, AppUserResetPasswordSchema, AppUserUpdateSchema
from .service import AppUserService

AppUserRouter = APIRouter(route_class=OperationLogRoute, prefix="/app_user", tags=["用户端用户模块"])


@AppUserRouter.get("/detail/{id}", summary="获取用户端用户详情", response_model=ResponseSchema[AppUserOutSchema])
async def get_obj_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:detail"]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await AppUserService(auth, db).detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取用户端用户详情成功")


@AppUserRouter.get("/list", summary="分页查询用户端用户", response_model=ResponseSchema[PageResultSchema[AppUserOutSchema]])
async def get_obj_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[AppUserQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await AppUserService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询用户端用户列表成功")


@AppUserRouter.put("/update/{id}", summary="修改用户端用户资料", response_model=ResponseSchema[AppUserOutSchema])
async def update_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:update"]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    data: Annotated[AppUserUpdateSchema, Body(description="修改用户端用户资料")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await AppUserService(auth, db).update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改用户端用户成功")


@AppUserRouter.patch("/status/batch", summary="批量修改用户端用户状态", response_model=ResponseSchema[None])
async def batch_set_available_obj_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:patch"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await AppUserService(auth, db).set_available(data=data)
    return SuccessResponse(msg="批量修改用户端用户状态成功")


@AppUserRouter.put("/password/reset/{id}", summary="重置用户端用户密码", response_model=ResponseSchema[AppUserOutSchema])
async def reset_password_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:reset_password"]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    data: Annotated[AppUserResetPasswordSchema, Body(description="重置用户端用户密码")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await AppUserService(auth, db).reset_password(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="重置用户端用户密码成功")


__all__ = ["AppUserRouter"]
