"""Schemas for the future App verification-code endpoint."""

from typing import Literal

from pydantic import BaseModel, Field

SmsScene = Literal["register_code", "login_code", "reset_password_code"]


class SmsSendCodeSchema(BaseModel):
    mobile: str = Field(..., min_length=7, max_length=20, description="手机号")
    scene: SmsScene = Field(..., description="短信场景")


class SmsSendCodeOutSchema(BaseModel):
    expires_in: int = Field(..., description="验证码有效期（秒）")
    resend_after: int = Field(..., description="再次发送等待时间（秒）")


__all__ = ["SmsScene", "SmsSendCodeOutSchema", "SmsSendCodeSchema"]
