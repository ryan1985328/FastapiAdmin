from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema
from app.core.exceptions import CustomException
from app.plugin.module_system.sms.constants import normalize_mobile


def _required_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name}不能为空")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalized_mobile(value: Any) -> str:
    try:
        return normalize_mobile(str(value or ""))
    except CustomException as exc:
        raise ValueError(exc.msg) from exc


class AppUserAddressCreateSchema(BaseModel):
    """当前 App 用户新增地址；用户身份不来自请求体。"""

    model_config = ConfigDict(extra="forbid")

    receiver_name: str = Field(..., max_length=128, description="收货人")
    receiver_mobile: str = Field(..., max_length=32, description="收货手机号")
    province: str = Field(..., max_length=128, description="省")
    city: str = Field(..., max_length=128, description="市")
    district: str = Field(..., max_length=128, description="区")
    detail_address: str = Field(..., max_length=512, description="详细地址")
    postal_code: str | None = Field(default=None, max_length=32, description="邮政编码")
    is_default: bool = Field(default=False, description="是否默认地址")

    @field_validator("receiver_name", "province", "city", "district", "detail_address", mode="before")
    @classmethod
    def validate_required_text(cls, value: Any, info) -> str:
        return _required_text(value, info.field_name)

    @field_validator("receiver_mobile", mode="before")
    @classmethod
    def validate_receiver_mobile(cls, value: Any) -> str:
        return _normalized_mobile(value)

    @field_validator("postal_code", mode="before")
    @classmethod
    def normalize_postal_code(cls, value: Any) -> str | None:
        return _optional_text(value)


class AppUserAddressUpdateSchema(BaseModel):
    """当前 App 用户编辑地址；不允许变更地址归属。"""

    model_config = ConfigDict(extra="forbid")

    receiver_name: str | None = Field(default=None, max_length=128, description="收货人")
    receiver_mobile: str | None = Field(default=None, max_length=32, description="收货手机号")
    province: str | None = Field(default=None, max_length=128, description="省")
    city: str | None = Field(default=None, max_length=128, description="市")
    district: str | None = Field(default=None, max_length=128, description="区")
    detail_address: str | None = Field(default=None, max_length=512, description="详细地址")
    postal_code: str | None = Field(default=None, max_length=32, description="邮政编码")
    is_default: bool | None = Field(default=None, description="是否默认地址")

    @field_validator("receiver_name", "province", "city", "district", "detail_address", mode="before")
    @classmethod
    def validate_optional_text(cls, value: Any, info) -> str | None:
        if value is None:
            return None
        return _required_text(value, info.field_name)

    @field_validator("receiver_mobile", mode="before")
    @classmethod
    def validate_optional_mobile(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalized_mobile(value)

    @field_validator("postal_code", mode="before")
    @classmethod
    def normalize_optional_postal_code(cls, value: Any) -> str | None:
        return _optional_text(value)


class AppUserAddressOutSchema(BaseModel):
    """App 地址响应，只暴露业务字段和地址 ID。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    receiver_name: str
    receiver_mobile: str
    province: str
    city: str
    district: str
    detail_address: str
    postal_code: str | None = None
    is_default: bool


class AppUserAddressUserSummarySchema(BaseModel):
    """Admin 地址列表/详情所需的最小 App User 摘要。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    mobile: str | None = None


class AppUserAddressAdminOutSchema(BaseSchema):
    """Admin 地址响应，保留系统审计字段供详情使用。"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    receiver_name: str
    receiver_mobile: str
    province: str
    city: str
    district: str
    detail_address: str
    postal_code: str | None = None
    is_default: bool
    app_user: AppUserAddressUserSummarySchema | None = None


class AppUserAddressQueryParam(BaseQueryParam):
    """Admin 地址业务查询参数。"""

    keyword: str | None = Field(
        default=None,
        description="关键词（用户ID、账号、昵称、用户手机号、收货人或收货手机号）",
        json_schema_extra={"q": "like"},
    )
    is_default: bool | None = Field(default=None, description="是否默认地址", json_schema_extra={"q": "eq"})
    user_id: int | None = Field(default=None, ge=1, description="App用户ID", json_schema_extra={"q": "eq"})
    province: str | None = Field(default=None, description="省", json_schema_extra={"q": "like"})
    city: str | None = Field(default=None, description="市", json_schema_extra={"q": "like"})
    district: str | None = Field(default=None, description="区", json_schema_extra={"q": "like"})


__all__ = [
    "AppUserAddressAdminOutSchema",
    "AppUserAddressCreateSchema",
    "AppUserAddressOutSchema",
    "AppUserAddressQueryParam",
    "AppUserAddressUpdateSchema",
    "AppUserAddressUserSummarySchema",
]
