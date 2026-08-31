"""Read-only Admin routes for SMS send logs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter

from .schema import SmsLogOutSchema, SmsLogQueryParam
from .service import SmsLogService

SmsLogRouter = APIRouter(prefix="/sms_log", tags=["短信记录模块"])


@SmsLogRouter.get("/detail/{id}", summary="获取短信记录详情", response_model=ResponseSchema[SmsLogOutSchema])
async def get_detail(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_log:detail"]))],
    id: Annotated[int, Path(ge=1, description="短信记录ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsLogService(auth, db).detail(id), msg="获取短信记录详情成功")


@SmsLogRouter.get("/list", summary="分页查询短信记录", response_model=ResponseSchema[PageResultSchema[SmsLogOutSchema]])
async def get_list(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_log:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[SmsLogQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await SmsLogService(auth, db).page(page.page_no, page.page_size, search, page.order_by)
    return SuccessResponse(data=result, msg="查询短信记录列表成功")


__all__ = ["SmsLogRouter"]
