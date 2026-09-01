
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter, redis_getter
from app.core.router_class import OperationLogRoute

from .schema import (
    AppUserBindReferrerSchema,
    AppUserOutSchema,
    AppUserQueryParam,
    AppUserReferralDescendantCountSchema,
    AppUserReferralNodeSchema,
    AppUserReferralSearchQueryParam,
    AppUserReferralSummarySchema,
    AppUserResetPasswordSchema,
    AppUserStatusActionSchema,
    AppUserUpdateSchema,
)
from .service import AppUserService

AppUserRouter = APIRouter(route_class=OperationLogRoute, prefix="/app_user", tags=["用户端用户模块"])
REFERRAL_PERMISSION = "module_system:app_user:referral"


@AppUserRouter.get(
    "/referral/search",
    summary="搜索推荐关系中心用户",
    response_model=ResponseSchema[PageResultSchema[AppUserReferralNodeSchema]],
)
async def referral_search_controller(
    _auth: Annotated[AuthSchema, Security(AuthPermission([REFERRAL_PERMISSION]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[AppUserReferralSearchQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserService(_auth, db).referral_search(
        search=search,
        page_no=page.page_no,
        page_size=page.page_size,
    )
    return SuccessResponse(data=result, msg="搜索推荐关系用户成功")


@AppUserRouter.get(
    "/referral/{id}",
    summary="获取用户推荐关系摘要",
    response_model=ResponseSchema[AppUserReferralSummarySchema],
)
async def referral_summary_controller(
    _auth: Annotated[AuthSchema, Security(AuthPermission([REFERRAL_PERMISSION]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserService(_auth, db).referral_summary(id=id)
    return SuccessResponse(data=result, msg="获取推荐关系摘要成功")


@AppUserRouter.get(
    "/referral/{id}/children",
    summary="分页获取用户直属下级",
    response_model=ResponseSchema[PageResultSchema[AppUserReferralNodeSchema]],
)
async def referral_children_controller(
    _auth: Annotated[AuthSchema, Security(AuthPermission([REFERRAL_PERMISSION]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    page: Annotated[PaginationQueryParam, Depends()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserService(_auth, db).referral_children(
        id=id,
        page_no=page.page_no,
        page_size=page.page_size,
    )
    return SuccessResponse(data=result, msg="获取直属下级成功")


@AppUserRouter.get(
    "/referral/{id}/descendant-count",
    summary="获取用户后代总数",
    response_model=ResponseSchema[AppUserReferralDescendantCountSchema],
)
async def referral_descendant_count_controller(
    _auth: Annotated[AuthSchema, Security(AuthPermission([REFERRAL_PERMISSION]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserService(_auth, db).referral_descendant_count(id=id)
    return SuccessResponse(data=result, msg="获取后代总数成功")


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


@AppUserRouter.patch("/status/{id}", summary="修改用户端用户状态", response_model=ResponseSchema[AppUserOutSchema])
async def change_status_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:patch"]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    data: Annotated[AppUserStatusActionSchema, Body(description="状态动作")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await AppUserService(auth, db).change_status(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改用户端用户状态成功")


@AppUserRouter.put("/password/reset/{id}", summary="重置用户端用户密码", response_model=ResponseSchema[AppUserOutSchema])
async def reset_password_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:reset_password"]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    data: Annotated[AppUserResetPasswordSchema, Body(description="重置用户端用户密码")],
    db: Annotated[AsyncSession, Depends(db_getter)],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result_dict = await AppUserService(auth, db, redis).reset_password(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="重置用户端用户密码成功")


@AppUserRouter.post("/referrer/bind/{id}", summary="绑定用户端用户推荐人", response_model=ResponseSchema[AppUserOutSchema])
async def bind_referrer_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user:bind_referrer"]))],
    id: Annotated[int, Path(description="用户端用户ID", ge=1)],
    data: Annotated[AppUserBindReferrerSchema, Body(description="推荐人绑定参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await AppUserService(auth, db).bind_referrer(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="绑定推荐人成功")


__all__ = ["AppUserRouter"]
