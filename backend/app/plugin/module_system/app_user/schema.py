from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseQueryParam
from app.core.validator import DateTimeStr
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

    keyword: str | None = Field(
        None,
        description="用户关键词（ID/登录账号/手机号/昵称/推荐码）",
        json_schema_extra={"q": "like"},
    )
    username: str | None = Field(None, description="登录账号", json_schema_extra={"q": "like"})
    nickname: str | None = Field(None, description="昵称", json_schema_extra={"q": "like"})
    mobile: str | None = Field(None, description="手机号", json_schema_extra={"q": "like"})
    id: int | None = Field(None, ge=1, description="用户端用户ID", json_schema_extra={"q": "eq"})
    status: AppUserStatus | None = Field(None, description="状态(0正常 1禁用 2冻结)", json_schema_extra={"q": "eq"})
    referral_code: str | None = Field(None, description="推荐码", json_schema_extra={"q": "like"})
    referrer: str | None = Field(None, description="推荐人用户名/手机号/昵称/推荐码", json_schema_extra={"q": "like"})
    has_referrer: bool | None = Field(None, description="是否已绑定推荐人", json_schema_extra={"q": "eq"})
    kyc_status: AppUserKycStatus | None = Field(None, description="实名状态", json_schema_extra={"q": "eq"})


class AppUserReferralSearchQueryParam(BaseModel):
    """Required search input for the relationship explorer."""

    keyword: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="用户ID/用户名/昵称/手机号/推荐码",
    )


class AppUserReferralNodeSchema(BaseModel):
    """Safe, masked relationship node used by search and lazy tree loading."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: str = Field(..., description="昵称")
    mobile: str | None = Field(default=None, description="掩码手机号")
    referral_code: str = Field(..., description="推荐码")
    status: int = Field(..., description="账号状态")
    kyc_status: AppUserKycStatus = Field(..., description="实名状态")
    direct_count: int = Field(default=0, ge=0, description="直属下级数量")
    has_children: bool = Field(default=False, description="是否存在直属下级")
    referrer_bound_at: DateTimeStr | None = Field(default=None, description="推荐关系绑定时间")


class AppUserReferralSummarySchema(AppUserReferralNodeSchema):
    """Current center user plus direct-referrer context and aggregate count."""

    referrer_id: int | None = Field(default=None, description="直接推荐人ID")
    referrer: AppUserReferralNodeSchema | None = Field(default=None, description="直接推荐人摘要")
    total_descendant_count: int = Field(default=0, ge=0, description="所有层级后代数量")


class AppUserReferralDescendantCountSchema(BaseModel):
    """Explicit count response for clients that only need the aggregate."""

    total_descendant_count: int = Field(default=0, ge=0, description="所有层级后代数量")


__all__ = [
    "AppUserOutSchema",
    "AppUserBindReferrerSchema",
    "AppUserReferralDescendantCountSchema",
    "AppUserReferralNodeSchema",
    "AppUserReferralSearchQueryParam",
    "AppUserReferralSummarySchema",
    "AppUserKycStatus",
    "AppUserQueryParam",
    "AppUserResetPasswordSchema",
    "AppUserStatus",
    "AppUserStatusActionSchema",
    "AppUserUpdateSchema",
]
