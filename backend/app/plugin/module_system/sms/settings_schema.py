"""Fixed two-provider SMS settings schemas.

The configuration surface is deliberately not a CRUD schema.  Each provider is
one built-in slot and the three authentication scenarios are fixed fields.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import SMS_PROVIDER_ALIYUN, SMS_PROVIDER_TENCENT

SmsProviderName = Literal[SMS_PROVIDER_ALIYUN, SMS_PROVIDER_TENCENT]
SmsSceneName = Literal["register_code", "login_code", "reset_password_code"]


def _strip(value: str | None) -> str:
    return str(value or "").strip()


class SmsTemplateSettingsSchema(BaseModel):
    """Fixed provider template identifiers for App authentication."""

    model_config = ConfigDict(extra="forbid")

    register_code: str = Field(default="", max_length=128, description="注册验证码模板编码或 ID")
    login_code: str = Field(default="", max_length=128, description="登录验证码模板编码或 ID")
    reset_password_code: str = Field(default="", max_length=128, description="重置密码验证码模板编码或 ID")

    @field_validator("register_code", "login_code", "reset_password_code", mode="before")
    @classmethod
    def strip_template_code(cls, value: str | None) -> str:
        return _strip(value)


class SmsProviderSettingsUpdateSchema(BaseModel):
    """Writable fields for one fixed provider slot."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=False, description="供应商是否启用")
    access_key_id: str = Field(default="", max_length=255, description="Aliyun AccessKey ID 或 Tencent SecretId")
    access_key_secret: str | None = Field(default=None, max_length=512, description="密钥；留空保留已有密文")
    sms_sdk_app_id: str | None = Field(default=None, max_length=64, description="Tencent Cloud SMS SDK App ID")
    sign_name: str = Field(default="", max_length=128, description="短信签名")
    templates: SmsTemplateSettingsSchema = Field(default_factory=SmsTemplateSettingsSchema, description="固定认证场景模板")

    @field_validator("access_key_id", "sign_name", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str:
        return _strip(value)

    @field_validator("access_key_secret", mode="before")
    @classmethod
    def strip_secret(cls, value: str | None) -> str | None:
        return None if value is None else _strip(value)

    @field_validator("sms_sdk_app_id", mode="before")
    @classmethod
    def strip_app_id(cls, value: str | None) -> str | None:
        value = _strip(value)
        return value or None


class SmsSettingsUpdateSchema(BaseModel):
    """Full settings payload for the two built-in providers."""

    model_config = ConfigDict(extra="forbid")

    sms_enabled: bool = Field(default=False, description="全局短信开关")
    active_provider: SmsProviderName = Field(default=SMS_PROVIDER_ALIYUN, description="当前短信供应商")
    aliyun: SmsProviderSettingsUpdateSchema = Field(default_factory=SmsProviderSettingsUpdateSchema)
    tencent: SmsProviderSettingsUpdateSchema = Field(default_factory=SmsProviderSettingsUpdateSchema)


class SmsTemplateSettingsOutSchema(SmsTemplateSettingsSchema):
    """Safe response for fixed template fields."""


class SmsProviderSettingsOutSchema(BaseModel):
    """Safe response for one provider; plaintext secrets never leave the API."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    access_key_id: str = ""
    has_secret: bool = False
    sms_sdk_app_id: str | None = None
    sign_name: str = ""
    templates: SmsTemplateSettingsOutSchema = Field(default_factory=SmsTemplateSettingsOutSchema)


class SmsSettingsOutSchema(BaseModel):
    sms_enabled: bool
    active_provider: SmsProviderName
    aliyun: SmsProviderSettingsOutSchema
    tencent: SmsProviderSettingsOutSchema


class SmsSettingsTestSendSchema(BaseModel):
    """Test one configured provider using one fixed authentication scenario."""

    model_config = ConfigDict(extra="forbid")

    provider: SmsProviderName
    mobile: str = Field(..., min_length=7, max_length=20, description="手机号")
    scene: SmsSceneName
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="测试验证码")

    @field_validator("mobile", "code", mode="before")
    @classmethod
    def strip_values(cls, value: str) -> str:
        return _strip(value)


class SmsSettingsTestSendResultSchema(BaseModel):
    provider: str
    success: bool
    code: str | None = None
    message: str | None = None
    request_id: str | None = None


__all__ = [
    "SmsProviderName",
    "SmsProviderSettingsOutSchema",
    "SmsProviderSettingsUpdateSchema",
    "SmsSceneName",
    "SmsSettingsOutSchema",
    "SmsSettingsTestSendResultSchema",
    "SmsSettingsTestSendSchema",
    "SmsSettingsUpdateSchema",
    "SmsTemplateSettingsOutSchema",
    "SmsTemplateSettingsSchema",
]
