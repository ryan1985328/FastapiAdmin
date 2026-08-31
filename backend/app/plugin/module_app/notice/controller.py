from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import PageResultSchema
from app.core.dependencies import db_getter

from .schema import AppNoticeDetailSchema, AppNoticeListItemSchema
from .service import AppNoticeService

AppNoticeRouter = APIRouter(prefix="/notices", tags=["App公共公告"])


@AppNoticeRouter.get(
    "",
    summary="获取App公告列表",
    response_model=ResponseSchema[PageResultSchema[AppNoticeListItemSchema]],
)
async def get_app_notice_list_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    page_no: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=50, description="每页数量")] = 10,
) -> JSONResponse:
    result = await AppNoticeService(db).page(page_no=page_no, page_size=page_size)
    return SuccessResponse(data=result, msg="获取公告列表成功")


@AppNoticeRouter.get(
    "/{id}",
    summary="获取App公告详情",
    response_model=ResponseSchema[AppNoticeDetailSchema],
)
async def get_app_notice_detail_controller(
    db: Annotated[AsyncSession, Depends(db_getter)],
    id: Annotated[int, Path(ge=1, description="公告ID")],
) -> JSONResponse:
    result = await AppNoticeService(db).detail(notice_id=id)
    return SuccessResponse(data=result, msg="获取公告详情成功")


__all__ = ["AppNoticeRouter"]
