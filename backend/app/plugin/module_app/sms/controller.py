"""Public App boundary for requesting verification SMS codes.

The App registration, login and password-reset services consume the same
``SmsService.verify_code`` lifecycle exposed by this endpoint.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import db_getter, redis_getter
from app.core.exceptions import CustomException
from app.plugin.module_system.sms.service import SmsService

from .schema import SmsSendCodeOutSchema, SmsSendCodeSchema

AppSmsRouter = APIRouter(prefix="/sms", tags=["App短信"])


@AppSmsRouter.post("/send-code", summary="发送短信验证码", response_model=ResponseSchema[SmsSendCodeOutSchema])
async def send_code(
    data: Annotated[SmsSendCodeSchema, Body(description="验证码发送参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    try:
        result = await SmsService(db, redis).send_code(mobile=data.mobile, scene=data.scene)
    except CustomException as exc:
        # A provider failure has already been audited in the request transaction.
        # Return the error response so the dependency can commit that audit row.
        if exc.status_code != 502:
            raise
        return ErrorResponse(msg=exc.msg, code=exc.code, status_code=exc.status_code, data=exc.data)
    return SuccessResponse(data=SmsSendCodeOutSchema(**result), msg="验证码发送成功")


__all__ = ["AppSmsRouter"]
