"""Dedicated SMS settings and operational test-send routes."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Security
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema
from app.core.dependencies import AuthPermission, db_getter, redis_getter
from app.core.exceptions import CustomException
from app.core.router_class import OperationLogRoute

from .service import SmsService
from .settings_schema import SmsSettingsOutSchema, SmsSettingsTestSendResultSchema, SmsSettingsTestSendSchema, SmsSettingsUpdateSchema
from .settings_service import SmsSettingsService

SmsSettingsRouter = APIRouter(route_class=OperationLogRoute, prefix="/sms", tags=["短信管理"])


@SmsSettingsRouter.get(
    "/settings",
    summary="获取短信配置",
    response_model=ResponseSchema[SmsSettingsOutSchema],
)
async def get_settings(
    _auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:sms_settings:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsSettingsService(_auth, db).get(), msg="获取短信配置成功")


@SmsSettingsRouter.put(
    "/settings",
    summary="保存短信配置",
    response_model=ResponseSchema[SmsSettingsOutSchema],
)
async def update_settings(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:sms_settings:update"]))],
    data: Annotated[SmsSettingsUpdateSchema, Body(description="短信固定双供应商配置")],
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await SmsSettingsService(auth, db).update(data, redis)
    return SuccessResponse(data=result, msg="短信配置保存成功")


@SmsSettingsRouter.post(
    "/settings/test-send",
    summary="测试发送短信",
    response_model=ResponseSchema[SmsSettingsTestSendResultSchema],
)
async def test_send(
    auth: Annotated[AuthSchema, Security(AuthPermission(["module_system:sms_settings:test_send"]))],
    data: Annotated[SmsSettingsTestSendSchema, Body(description="短信供应商测试发送")],
    redis: Annotated[Redis, Depends(redis_getter)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    try:
        result = await SmsService(db, redis, auth).test_send(
            mobile=data.mobile,
            scene=data.scene,
            params={"code": data.code},
            provider=data.provider,
        )
    except CustomException as exc:
        if exc.status_code != 502:
            raise
        return ErrorResponse(msg=exc.msg, code=exc.code, status_code=exc.status_code, data=exc.data)
    normalized = SmsSettingsTestSendResultSchema(
        provider=result.provider,
        success=result.success,
        code=result.code,
        message=result.message,
        request_id=result.request_id,
    )
    if not result.success:
        return ErrorResponse(msg=f"短信发送失败: {result.message or result.code or '供应商返回失败'}", status_code=502)
    return SuccessResponse(data=normalized, msg="短信测试发送成功")


__all__ = ["SmsSettingsRouter"]
