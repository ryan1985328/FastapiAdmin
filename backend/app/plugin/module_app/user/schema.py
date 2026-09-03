from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseSchema, JWTOutSchema
from app.core.validator import DateTimeStr

from .constants import AppUserKycStatus, AppUserStatus
from .referral import normalize_referral_code


class AppUserCreateSchema(BaseModel):
    """Public registration payload, with legacy username compatibility."""

    username: str | None = Field(default=None, min_length=3, max_length=64, pattern=r"^[A-Za-z][A-Za-z0-9_.-]*$", description="兼容登录账号")
    password: str = Field(..., min_length=6, max_length=128, description="登录密码")
    nickname: str | None = Field(default=None, max_length=128, description="昵称")
    avatar: str | None = Field(default=None, max_length=512, description="头像URL地址")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")
    code: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$", description="注册短信验证码")
    referral_code: str | None = Field(default=None, min_length=4, max_length=32, description="推荐码")

    @field_validator("referral_code")
    @classmethod
    def normalize_registration_referral_code(cls, value: str | None) -> str | None:
        return normalize_referral_code(value) if value is not None else None


class AppUserProfileUpdateSchema(BaseModel):
    """Fields an App user may edit for their own profile."""

    nickname: str = Field(..., min_length=1, max_length=128, description="昵称")

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("昵称不能为空")
        return normalized


class AppLoginSchema(BaseModel):
    """Legacy App username/password login payload."""

    username: str = Field(..., min_length=1, max_length=64, description="登录账号")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码")


class AppRefreshTokenSchema(BaseModel):
    """Refresh token payload."""

    refresh_token: str = Field(..., min_length=1, description="刷新令牌")


class AppMobilePasswordLoginSchema(BaseModel):
    """Primary App mobile/password login payload."""

    mobile: str = Field(..., min_length=7, max_length=20, description="手机号")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码")


class AppMobileSmsLoginSchema(BaseModel):
    """App mobile/SMS login payload."""

    mobile: str = Field(..., min_length=7, max_length=20, description="手机号")
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="短信验证码")


class AppResetPasswordSchema(BaseModel):
    """Unauthenticated mobile/SMS password reset payload."""

    mobile: str = Field(..., min_length=7, max_length=20, description="手机号")
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="短信验证码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class AppChangePasswordSchema(BaseModel):
    """Authenticated password change payload."""

    current_password: str = Field(..., min_length=1, max_length=128, description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class AppUserOutSchema(BaseSchema):
    """Business User summary; never exposes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    username: str = Field(..., description="登录账号")
    nickname: str = Field(..., description="昵称")
    avatar: str | None = Field(default=None, description="头像URL地址")
    mobile: str | None = Field(default=None, description="手机号")
    status: AppUserStatus = Field(default=AppUserStatus.ACTIVE, description="状态(0正常 1禁用 2冻结)")
    referral_code: str = Field(..., description="稳定唯一推荐码")
    referrer_id: int | None = Field(default=None, description="直接推荐人ID")
    referrer_bound_at: DateTimeStr | None = Field(default=None, description="推荐关系绑定时间")
    referrer: "AppUserReferrerSummarySchema | None" = Field(default=None, description="推荐人摘要")
    has_referrer: bool = Field(default=False, description="是否已绑定推荐人")
    kyc_status: AppUserKycStatus = Field(default=AppUserKycStatus.UNVERIFIED, description="实名聚合状态")
    kyc_reviewed_at: DateTimeStr | None = Field(default=None, description="实名审核时间")


class AppUserReferrerSummarySchema(BaseModel):
    """Small referrer projection used in App/Admin user summaries."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="推荐人ID")
    username: str = Field(..., description="推荐人用户名")
    nickname: str = Field(..., description="推荐人昵称")
    mobile: str | None = Field(default=None, description="推荐人手机号")
    referral_code: str = Field(..., description="推荐人推荐码")


class AppUserStatusActionSchema(BaseModel):
    """One explicit, legal Business User status action."""

    action: Literal["enable", "disable", "freeze", "unfreeze"] = Field(..., description="状态动作")


class AppUserBindReferrerSchema(BaseModel):
    """Bind a previously unbound user to a referrer by referral code."""

    referral_code: str = Field(..., min_length=4, max_length=32, description="推荐人推荐码")

    @field_validator("referral_code")
    @classmethod
    def normalize_referral_code(cls, value: str) -> str:
        return normalize_referral_code(value)


class AppLoginOutSchema(JWTOutSchema):
    """App login response."""

    user_info: AppUserOutSchema = Field(..., description="当前App用户")


__all__ = [
    "AppLoginOutSchema",
    "AppChangePasswordSchema",
    "AppLoginSchema",
    "AppMobilePasswordLoginSchema",
    "AppMobileSmsLoginSchema",
    "AppRefreshTokenSchema",
    "AppResetPasswordSchema",
    "AppUserBindReferrerSchema",
    "AppUserCreateSchema",
    "AppUserOutSchema",
    "AppUserProfileUpdateSchema",
    "AppUserReferrerSummarySchema",
    "AppUserStatusActionSchema",
]
