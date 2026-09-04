from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import PageResultSchema
from app.core.dependencies import db_getter
from app.plugin.module_app.auth.dependencies import get_current_app_user
from app.plugin.module_app.user.model import AppUserModel
from app.plugin.module_product.order.schema import AppOrderCreateSchema, AppOrderSchema
from app.plugin.module_product.order.service import ProductOrderService

AppOrderRouter = APIRouter(prefix="/order", tags=["App商城订单"])


@AppOrderRouter.post("", summary="创建App商城订单", response_model=ResponseSchema[AppOrderSchema])
async def create_app_order_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    data: Annotated[AppOrderCreateSchema, Body(description="商品ID与购买数量")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await ProductOrderService(db).create(user.id, data)
    return SuccessResponse(data=result, msg="创建订单成功")


@AppOrderRouter.get(
    "/list",
    summary="查询我的商城订单",
    response_model=ResponseSchema[PageResultSchema[AppOrderSchema]],
)
async def list_my_orders_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    page_no: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=50, description="每页数量")] = 10,
) -> JSONResponse:
    result = await ProductOrderService(db).list_owned(user.id, page_no=page_no, page_size=page_size)
    return SuccessResponse(data=result, msg="查询我的订单成功")


@AppOrderRouter.post("/{id}/pay", summary="Development Payment支付订单", response_model=ResponseSchema[AppOrderSchema])
async def pay_app_order_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(ge=1, description="订单ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await ProductOrderService(db).pay(user.id, id)
    return SuccessResponse(data=result, msg="Development Payment支付成功")


@AppOrderRouter.post("/{id}/cancel", summary="取消待支付订单", response_model=ResponseSchema[AppOrderSchema])
async def cancel_app_order_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(ge=1, description="订单ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await ProductOrderService(db).cancel(user.id, id)
    return SuccessResponse(data=result, msg="取消订单成功")


@AppOrderRouter.get("/{id}", summary="获取我的商城订单详情", response_model=ResponseSchema[AppOrderSchema])
async def get_my_order_detail_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(ge=1, description="订单ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await ProductOrderService(db).detail_owned(user.id, id)
    return SuccessResponse(data=result, msg="获取订单详情成功")


__all__ = ["AppOrderRouter"]
