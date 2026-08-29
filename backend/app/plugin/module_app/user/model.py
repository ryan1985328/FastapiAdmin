from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class AppUserModel(ModelMixin):
    """C-end user account, intentionally independent from ``sys_user``."""

    __tablename__: str = "app_user"
    __table_args__: dict[str, str] = {"comment": "C端用户表"}

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="登录账号")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    nickname: Mapped[str] = mapped_column(String(128), nullable=False, comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="头像URL地址")
    mobile: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="手机号")
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="状态(0启用 1停用)")


__all__ = ["AppUserModel"]
