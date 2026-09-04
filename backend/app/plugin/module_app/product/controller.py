from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import PageResultSchema
from app.core.dependencies import db_getter

from .schema import AppProductDetailSchema, AppProductListItemSchema
from .service import AppProductService

AppProductRouter = APIRouter(prefix="/product", tags=["App商城商品"])


@AppProductRouter.get(
    "/list",
    summary="获取App商城商品列表",
    response_model=ResponseSchema[PageResultSchema[AppProductListItemSchema]],
)
async def list_app_products_controller(
    request: Request,
    db: Annotated[AsyncSession, Depends(db_getter)],
    page_no: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=50, description="每页数量")] = 10,
    keyword: Annotated[str | None, Query(max_length=128, description="商品关键词")] = None,
) -> JSONResponse:
    result = await AppProductService(db).page(request, page_no=page_no, page_size=page_size, keyword=keyword)
    return SuccessResponse(data=result, msg="获取商城商品列表成功")


@AppProductRouter.get("/{id}/cover", summary="获取App商城商品封面", response_model=None)
async def get_app_product_cover_controller(
    id: Annotated[int, Path(ge=1, description="商品ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> Response:
    return await AppProductService(db).cover(product_id=id)


@AppProductRouter.get(
    "/{id}",
    summary="获取App商城商品详情",
    response_model=ResponseSchema[AppProductDetailSchema],
)
async def get_app_product_detail_controller(
    request: Request,
    id: Annotated[int, Path(ge=1, description="商品ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppProductService(db).detail(request, product_id=id)
    return SuccessResponse(data=result, msg="获取商城商品详情成功")


__all__ = ["AppProductRouter"]
