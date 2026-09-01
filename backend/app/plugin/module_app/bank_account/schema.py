import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema
from app.plugin.module_app.user.constants import AppUserKycStatus

from .constants import AppUserBankAccountStatus


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


def _normalize_card_number(value: Any) -> str:
    card_number = re.sub(r"[\s-]+", "", str(value or ""))
    if not re.fullmatch(r"\d{12,19}", card_number):
        # Do not include the supplied value in a validation error or log.
        raise ValueError("银行卡号格式不正确，请输入12-19位数字")
    return card_number


class AppUserBankAccountCreateSchema(BaseModel):
    """Current App user bank account input; ownership/status are server-owned."""

    model_config = ConfigDict(extra="forbid")

    bank_name: str = Field(..., max_length=128, description="银行名称")
    bank_code: str | None = Field(default=None, max_length=64, description="银行代码")
    account_name: str = Field(..., max_length=128, description="持卡人姓名")
    card_number: str = Field(..., description="银行卡号")
    branch_name: str | None = Field(default=None, max_length=128, description="开户支行")
    is_default: bool = Field(default=False, description="是否默认银行卡")

    @field_validator("bank_name", "account_name", mode="before")
    @classmethod
    def validate_required_text(cls, value: Any, info) -> str:
        return _required_text(value, info.field_name)

    @field_validator("bank_code", "branch_name", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Any) -> str | None:
        return _optional_text(value)

    @field_validator("card_number", mode="before")
    @classmethod
    def normalize_card_number(cls, value: Any) -> str:
        return _normalize_card_number(value)


class AppUserBankAccountUpdateSchema(BaseModel):
    """Current App user edit input; a supplied card number means replacement."""

    model_config = ConfigDict(extra="forbid")

    bank_name: str | None = Field(default=None, max_length=128, description="银行名称")
    bank_code: str | None = Field(default=None, max_length=64, description="银行代码")
    account_name: str | None = Field(default=None, max_length=128, description="持卡人姓名")
    card_number: str | None = Field(default=None, description="更换后的银行卡号")
    branch_name: str | None = Field(default=None, max_length=128, description="开户支行")
    is_default: bool | None = Field(default=None, description="是否默认银行卡")

    @field_validator("bank_name", "account_name", mode="before")
    @classmethod
    def validate_optional_required_text(cls, value: Any, info) -> str | None:
        if value is None:
            return None
        return _required_text(value, info.field_name)

    @field_validator("bank_code", "branch_name", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Any) -> str | None:
        return _optional_text(value)

    @field_validator("card_number", mode="before")
    @classmethod
    def normalize_optional_card_number(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_card_number(value)


class AppUserBankAccountOutSchema(BaseModel):
    """Safe App projection; no user ID, ciphertext, or full card number."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_name: str
    bank_code: str | None = None
    account_name: str
    masked_card_number: str
    branch_name: str | None = None
    is_default: bool
    status: AppUserBankAccountStatus


class AppUserBankAccountUserSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    mobile: str | None = None
    kyc_status: AppUserKycStatus = AppUserKycStatus.UNVERIFIED


class AppUserBankAccountAdminOutSchema(BaseSchema):
    """Safe Admin projection with the minimum App User and KYC summary."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    bank_name: str
    bank_code: str | None = None
    account_name: str
    masked_card_number: str
    branch_name: str | None = None
    is_default: bool
    status: AppUserBankAccountStatus
    app_user: AppUserBankAccountUserSummarySchema | None = None


class AppUserBankAccountQueryParam(BaseQueryParam):
    """Admin query fields; card search is limited to the stored last four digits."""

    keyword: str | None = Field(
        default=None,
        description="关键词（用户ID、账号、昵称、手机号、持卡人、银行、卡号末四位）",
        json_schema_extra={"q": "like"},
    )
    user_id: int | None = Field(default=None, ge=1, description="App用户ID", json_schema_extra={"q": "eq"})
    bank_name: str | None = Field(default=None, description="银行名称", json_schema_extra={"q": "like"})
    account_name: str | None = Field(default=None, description="持卡人", json_schema_extra={"q": "like"})
    branch_name: str | None = Field(default=None, description="开户支行", json_schema_extra={"q": "like"})
    is_default: bool | None = Field(default=None, description="是否默认银行卡", json_schema_extra={"q": "eq"})
    status: AppUserBankAccountStatus | None = Field(default=None, description="银行卡状态", json_schema_extra={"q": "eq"})
    kyc_status: AppUserKycStatus | None = Field(default=None, description="实名状态", json_schema_extra={"q": "eq"})


class AppUserBankAccountStatusActionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["enable", "disable"]


__all__ = [
    "AppUserBankAccountAdminOutSchema",
    "AppUserBankAccountCreateSchema",
    "AppUserBankAccountOutSchema",
    "AppUserBankAccountQueryParam",
    "AppUserBankAccountStatusActionSchema",
    "AppUserBankAccountUpdateSchema",
    "AppUserBankAccountUserSummarySchema",
]
