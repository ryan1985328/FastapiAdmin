from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseSchema, JWTOutSchema


class AppUserCreateSchema(BaseModel):
    """Public registration payload."""

    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[A-Za-z][A-Za-z0-9_.-]*$", description="登录账号")
    password: str = Field(..., min_length=6, max_length=128, description="登录密码")
    nickname: str | None = Field(default=None, max_length=128, description="昵称")
    avatar: str | None = Field(default=None, max_length=512, description="头像URL地址")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")


class AppLoginSchema(BaseModel):
    """App account/password login payload."""

    username: str = Field(..., min_length=1, max_length=64, description="登录账号")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码")


class AppRefreshTokenSchema(BaseModel):
    """Refresh token payload."""

    refresh_token: str = Field(..., min_length=1, description="刷新令牌")


class AppUserOutSchema(BaseSchema):
    """Safe App user representation; never exposes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    username: str = Field(..., description="登录账号")
    nickname: str = Field(..., description="昵称")
    avatar: str | None = Field(default=None, description="头像URL地址")
    mobile: str | None = Field(default=None, description="手机号")
    status: int = Field(default=0, description="状态(0启用 1停用)")


class AppLoginOutSchema(JWTOutSchema):
    """App login response."""

    user_info: AppUserOutSchema = Field(..., description="当前App用户")


__all__ = [
    "AppLoginOutSchema",
    "AppLoginSchema",
    "AppRefreshTokenSchema",
    "AppUserCreateSchema",
    "AppUserOutSchema",
]
