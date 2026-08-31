"""Admin routes for SMS channels."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter, redis_getter

from .schema import SmsChannelCreateSchema, SmsChannelOutSchema, SmsChannelQueryParam, SmsChannelUpdateSchema, SmsTestSendResultSchema, SmsTestSendSchema
from .service import SmsChannelService

SmsChannelRouter = APIRouter(prefix="/sms_channel", tags=["短信渠道模块"])


@SmsChannelRouter.get("/detail/{id}", summary="获取短信渠道详情", response_model=ResponseSchema[SmsChannelOutSchema])
async def get_detail(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_channel:detail"]))],
    id: Annotated[int, Path(ge=1, description="短信渠道ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsChannelService(auth, db).detail(id), msg="获取短信渠道详情成功")


@SmsChannelRouter.get("/list", summary="分页查询短信渠道", response_model=ResponseSchema[PageResultSchema[SmsChannelOutSchema]])
async def get_list(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_channel:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[SmsChannelQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await SmsChannelService(auth, db).page(page.page_no, page.page_size, search, page.order_by)
    return SuccessResponse(data=result, msg="查询短信渠道列表成功")


@SmsChannelRouter.post("/create", status_code=201, summary="创建短信渠道", response_model=ResponseSchema[SmsChannelOutSchema])
async def create(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_channel:create"]))],
    data: Annotated[SmsChannelCreateSchema, Body(description="创建参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsChannelService(auth, db).create(data), msg="创建短信渠道成功", status_code=201)


@SmsChannelRouter.put("/update/{id}", summary="修改短信渠道", response_model=ResponseSchema[SmsChannelOutSchema])
async def update(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_channel:update"]))],
    id: Annotated[int, Path(ge=1, description="短信渠道ID")],
    data: Annotated[SmsChannelUpdateSchema, Body(description="修改参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsChannelService(auth, db).update(id, data), msg="修改短信渠道成功")


@SmsChannelRouter.patch("/status/batch", summary="批量修改短信渠道状态", response_model=ResponseSchema[None])
async def set_available(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_channel:patch"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await SmsChannelService(auth, db).set_available(data)
    return SuccessResponse(msg="修改短信渠道状态成功")


@SmsChannelRouter.patch("/default/{id}", summary="设为默认短信渠道", response_model=ResponseSchema[SmsChannelOutSchema])
async def set_default(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_channel:default"]))],
    id: Annotated[int, Path(ge=1, description="短信渠道ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsChannelService(auth, db).set_default(id), msg="默认短信渠道设置成功")


@SmsChannelRouter.post("/test-send/{id}", summary="测试发送短信", response_model=ResponseSchema[SmsTestSendResultSchema])
async def test_send(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_channel:test_send"]))],
    id: Annotated[int, Path(ge=1, description="短信渠道ID")],
    data: Annotated[SmsTestSendSchema, Body(description="测试发送参数")],
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await SmsChannelService(auth, db).test_send(id, data, redis)
    if not result.success:
        # Keep the flushed failure audit row in the request transaction.
        return ErrorResponse(msg=f"短信发送失败: {result.message or result.code or '供应商返回失败'}", status_code=502)
    return SuccessResponse(data=result, msg="短信测试发送成功")


__all__ = ["SmsChannelRouter"]
