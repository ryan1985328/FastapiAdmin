from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter

from .schema import ProductOrderAdminDetailSchema, ProductOrderAdminItemSchema, ProductOrderQueryParam
from .service import ProductOrderService

ProductOrderRouter = APIRouter(prefix="/order", tags=["商城订单管理"])


@ProductOrderRouter.get(
    "/list",
    summary="分页查询商城订单",
    response_model=ResponseSchema[PageResultSchema[ProductOrderAdminItemSchema]],
)
async def get_product_order_list_controller(
    _auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:order:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[ProductOrderQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await ProductOrderService(db).admin_page(
        search=search,
        page_no=page.page_no,
        page_size=page.page_size,
    )
    return SuccessResponse(data=result, msg="查询商城订单列表成功")


@ProductOrderRouter.get(
    "/detail/{id}",
    summary="获取商城订单详情",
    response_model=ResponseSchema[ProductOrderAdminDetailSchema],
)
async def get_product_order_detail_controller(
    _auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:order:detail"]))],
    id: Annotated[int, Path(ge=1, description="订单ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await ProductOrderService(db).admin_detail(id)
    return SuccessResponse(data=result, msg="获取商城订单详情成功")


__all__ = ["ProductOrderRouter"]
