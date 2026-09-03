"""Schemas for SMS template administration."""

import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema
from app.plugin.module_system.sms.constants import SMS_SCENES

SmsProviderName = Literal["aliyun", "tencent"]
_PARAMETER_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def _parse_param_schema(value: object) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError('模板参数必须是 JSON 数组，例如 ["code"]') from exc
    if not isinstance(value, list):
        raise ValueError("模板参数必须是字符串数组")
    result: list[str] = []
    for item in value:
        name = str(item).strip()
        if not _PARAMETER_NAME.fullmatch(name):
            raise ValueError(f"模板参数名不合法: {name}")
        if name in result:
            raise ValueError(f"模板参数名重复: {name}")
        result.append(name)
    return result


def _scene(value: str) -> str:
    scene = str(value or "").strip()
    if scene not in SMS_SCENES:
        raise ValueError(f"短信场景不受支持: {scene}")
    return scene


class SmsTemplateCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="模板名称")
    scene: str = Field(..., description="业务场景")
    provider: SmsProviderName = Field(..., description="供应商")
    provider_template_code: str = Field(..., min_length=1, max_length=128, description="供应商模板编码")
    param_schema: list[str] = Field(default_factory=lambda: ["code"], description="允许的模板参数名")
    status: int = Field(default=0, ge=0, le=1, description="状态（0启用 1停用）")

    @field_validator("name", "provider_template_code")
    @classmethod
    def strip_text(cls, value: str, info) -> str:
        value = str(value).strip()
        if not value:
            raise ValueError(f"{info.field_name}不能为空")
        return value

    @field_validator("scene")
    @classmethod
    def validate_scene(cls, value: str) -> str:
        return _scene(value)

    @field_validator("param_schema", mode="before")
    @classmethod
    def validate_params(cls, value: object) -> list[str]:
        return _parse_param_schema(value)


class SmsTemplateUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64, description="模板名称")
    scene: str | None = Field(default=None, description="业务场景")
    provider: SmsProviderName | None = Field(default=None, description="供应商")
    provider_template_code: str | None = Field(default=None, min_length=1, max_length=128, description="供应商模板编码")
    param_schema: list[str] | None = Field(default=None, description="允许的模板参数名")
    status: int | None = Field(default=None, ge=0, le=1, description="状态（0启用 1停用）")

    @field_validator("name", "provider_template_code")
    @classmethod
    def strip_optional_text(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        if not value:
            raise ValueError(f"{info.field_name}不能为空")
        return value

    @field_validator("scene")
    @classmethod
    def validate_optional_scene(cls, value: str | None) -> str | None:
        return _scene(value) if value is not None else None

    @field_validator("param_schema", mode="before")
    @classmethod
    def validate_optional_params(cls, value: object) -> list[str] | None:
        return _parse_param_schema(value) if value is not None else None


class SmsTemplateOutSchema(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    name: str
    scene: str
    provider: str
    provider_template_code: str
    param_schema: list[str]
    status: int


class SmsTemplateQueryParam(BaseQueryParam):
    name: str | None = Field(default=None, description="模板名称", json_schema_extra={"q": "like"})
    scene: str | None = Field(default=None, description="业务场景", json_schema_extra={"q": "eq"})
    provider: SmsProviderName | None = Field(default=None, description="供应商", json_schema_extra={"q": "eq"})
    status: int | None = Field(default=None, ge=0, le=1, description="状态", json_schema_extra={"q": "eq"})


__all__ = [
    "SmsTemplateCreateSchema",
    "SmsTemplateOutSchema",
    "SmsTemplateQueryParam",
    "SmsTemplateUpdateSchema",
]
