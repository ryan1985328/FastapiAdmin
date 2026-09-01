from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Security
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import AppUserAddressAdminOutSchema, AppUserAddressQueryParam
from .service import AppUserAddressService

AppUserAddressRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/app_user_address",
    tags=["用户地址模块"],
)


@AppUserAddressRouter.get(
    "/detail/{id}",
    summary="获取用户地址详情",
    response_model=ResponseSchema[AppUserAddressAdminOutSchema],
)
async def get_obj_detail_controller(
    _auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user_address:detail"]))],
    id: Annotated[int, Path(description="用户地址ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserAddressService(_auth, db).detail(id)
    return SuccessResponse(data=result, msg="获取用户地址详情成功")


@AppUserAddressRouter.get(
    "/list",
    summary="分页查询用户地址",
    response_model=ResponseSchema[PageResultSchema[AppUserAddressAdminOutSchema]],
)
async def get_obj_list_controller(
    _auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:app_user_address:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[AppUserAddressQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserAddressService(_auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询用户地址列表成功")


__all__ = ["AppUserAddressRouter"]
