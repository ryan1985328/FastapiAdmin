from pydantic import BaseModel, Field

from app.core.base_schema import BaseQueryParam
from app.plugin.module_app.user.constants import AppUserKycStatus, AppUserStatus
from app.plugin.module_app.user.schema import (
    AppUserBindReferrerSchema,
    AppUserOutSchema,
    AppUserStatusActionSchema,
)


class AppUserUpdateSchema(BaseModel):
    """Admin-editable App user profile fields.

    Account identity and password are intentionally excluded. Account creation
    and password changes remain in the App auth flow / reset endpoint.
    """

    nickname: str | None = Field(default=None, max_length=128, description="昵称")
    avatar: str | None = Field(default=None, max_length=512, description="头像URL地址")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")


class AppUserResetPasswordSchema(BaseModel):
    """Admin password reset payload; only the plaintext input is accepted."""

    password: str = Field(..., min_length=6, max_length=128, description="新密码")


class AppUserQueryParam(BaseQueryParam):
    """App user list filters."""

    username: str | None = Field(None, description="登录账号", json_schema_extra={"q": "like"})
    nickname: str | None = Field(None, description="昵称", json_schema_extra={"q": "like"})
    mobile: str | None = Field(None, description="手机号", json_schema_extra={"q": "like"})
    id: int | None = Field(None, ge=1, description="用户端用户ID", json_schema_extra={"q": "eq"})
    status: AppUserStatus | None = Field(None, description="状态(0正常 1禁用 2冻结)", json_schema_extra={"q": "eq"})
    referral_code: str | None = Field(None, description="推荐码", json_schema_extra={"q": "like"})
    referrer: str | None = Field(None, description="推荐人用户名/手机号/昵称/推荐码", json_schema_extra={"q": "like"})
    kyc_status: AppUserKycStatus | None = Field(None, description="实名状态", json_schema_extra={"q": "eq"})


__all__ = [
    "AppUserOutSchema",
    "AppUserBindReferrerSchema",
    "AppUserKycStatus",
    "AppUserQueryParam",
    "AppUserResetPasswordSchema",
    "AppUserStatus",
    "AppUserStatusActionSchema",
    "AppUserUpdateSchema",
]
