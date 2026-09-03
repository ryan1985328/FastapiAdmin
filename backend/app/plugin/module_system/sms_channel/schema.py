"""Schemas for SMS channel administration."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema

SmsProviderName = Literal["aliyun", "tencent"]


def _required_text(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name}不能为空")
    return text


class SmsChannelCreateSchema(BaseModel):
    """创建渠道；secret 只在写请求中接收。"""

    name: str = Field(..., min_length=1, max_length=64, description="渠道名称")
    provider: SmsProviderName = Field(..., description="供应商")
    access_key_id: str = Field(..., min_length=1, max_length=255, description="AccessKey ID")
    access_key_secret: str = Field(..., min_length=1, max_length=512, description="AccessKey Secret")
    sms_sdk_app_id: str | None = Field(default=None, max_length=64, description="腾讯云短信 SDK App ID")
    sign_name: str = Field(..., min_length=1, max_length=128, description="短信签名")
    status: int = Field(default=0, ge=0, le=1, description="状态（0启用 1停用）")
    is_default: bool = Field(default=False, description="是否默认渠道")

    @field_validator("name", "access_key_id", "access_key_secret", "sign_name")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _required_text(value, info.field_name)


class SmsChannelUpdateSchema(BaseModel):
    """更新渠道；secret 为空表示保留原密文。"""

    name: str | None = Field(default=None, min_length=1, max_length=64, description="渠道名称")
    provider: SmsProviderName | None = Field(default=None, description="供应商")
    access_key_id: str | None = Field(default=None, min_length=1, max_length=255, description="AccessKey ID")
    access_key_secret: str | None = Field(default=None, max_length=512, description="新 AccessKey Secret")
    sms_sdk_app_id: str | None = Field(default=None, max_length=64, description="腾讯云短信 SDK App ID")
    sign_name: str | None = Field(default=None, min_length=1, max_length=128, description="短信签名")
    status: int | None = Field(default=None, ge=0, le=1, description="状态（0启用 1停用）")
    is_default: bool | None = Field(default=None, description="是否默认渠道")

    @field_validator("name", "access_key_id", "sms_sdk_app_id", "sign_name")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _required_text(value, info.field_name) if value is not None else None

    @field_validator("access_key_secret")
    @classmethod
    def normalize_secret(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class SmsChannelOutSchema(BaseSchema):
    """Safe channel response; the secret is deliberately absent."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    provider: str
    access_key_id: str
    sms_sdk_app_id: str | None = None
    sign_name: str
    status: int
    is_default: bool
    has_secret: bool = Field(default=False, description="是否已配置 Secret")


class SmsChannelQueryParam(BaseQueryParam):
    """渠道列表筛选条件。"""

    name: str | None = Field(default=None, description="渠道名称", json_schema_extra={"q": "like"})
    provider: SmsProviderName | None = Field(default=None, description="供应商", json_schema_extra={"q": "eq"})
    status: int | None = Field(default=None, ge=0, le=1, description="状态", json_schema_extra={"q": "eq"})


class SmsTestSendSchema(BaseModel):
    """Admin test-send request; provider/template are resolved server-side."""

    mobile: str = Field(..., min_length=7, max_length=20, description="手机号")
    scene: str = Field(..., description="短信场景")
    params: dict[str, str | int | float | bool] = Field(default_factory=dict, description="模板参数")


class SmsTestSendResultSchema(BaseModel):
    provider: str
    success: bool
    code: str | None = None
    message: str | None = None
    request_id: str | None = None


__all__ = [
    "SmsChannelCreateSchema",
    "SmsChannelOutSchema",
    "SmsChannelQueryParam",
    "SmsChannelUpdateSchema",
    "SmsProviderName",
    "SmsTestSendResultSchema",
    "SmsTestSendSchema",
]
