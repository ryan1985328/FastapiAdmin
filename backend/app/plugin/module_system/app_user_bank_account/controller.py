from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Security
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import (
    AppUserBankAccountAdminOutSchema,
    AppUserBankAccountQueryParam,
    AppUserBankAccountStatusActionSchema,
)
from .service import AppUserBankAccountService

AppUserBankAccountRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/app_user_bank_account",
    tags=["用户银行卡模块"],
)


@AppUserBankAccountRouter.get(
    "/detail/{id}",
    summary="获取用户银行卡详情",
    response_model=ResponseSchema[AppUserBankAccountAdminOutSchema],
)
async def get_obj_detail_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user_bank_account:detail"]))],
    id: Annotated[int, Path(description="用户银行卡ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(auth, db).detail(id)
    return SuccessResponse(data=result, msg="获取用户银行卡详情成功")


@AppUserBankAccountRouter.get(
    "/list",
    summary="分页查询用户银行卡",
    response_model=ResponseSchema[PageResultSchema[AppUserBankAccountAdminOutSchema]],
)
async def get_obj_list_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user_bank_account:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[AppUserBankAccountQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询用户银行卡列表成功")


@AppUserBankAccountRouter.patch(
    "/status/{id}",
    summary="启用或禁用用户银行卡",
    response_model=ResponseSchema[AppUserBankAccountAdminOutSchema],
)
async def change_status_controller(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user_bank_account:patch"]))],
    id: Annotated[int, Path(description="用户银行卡ID", ge=1)],
    data: Annotated[AppUserBankAccountStatusActionSchema, Body(description="银行卡状态动作")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(auth, db).change_status(id, data.action)
    return SuccessResponse(data=result, msg="修改用户银行卡状态成功")


__all__ = ["AppUserBankAccountRouter"]
