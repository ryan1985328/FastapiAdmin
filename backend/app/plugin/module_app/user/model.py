from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin

from .constants import AppUserStatus
from .referral import generate_referral_code


class AppUserModel(ModelMixin):
    """C-end user account, intentionally independent from ``sys_user``."""

    __tablename__: str = "app_user"
    __table_args__: dict[str, str] = {"comment": "C端用户表"}

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="登录账号")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    nickname: Mapped[str] = mapped_column(String(128), nullable=False, comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="头像URL地址")
    mobile: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="手机号")
    status: Mapped[int] = mapped_column(
        Integer,
        default=AppUserStatus.ACTIVE,
        nullable=False,
        comment="状态(0正常 1禁用 2冻结)",
    )
    referral_code: Mapped[str] = mapped_column(
        String(16),
        unique=True,
        nullable=False,
        default=generate_referral_code,
        comment="稳定唯一推荐码",
    )
    referrer_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("app_user.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
        comment="直接推荐人ID",
    )
    referrer_bound_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="推荐关系绑定时间",
    )


__all__ = ["AppUserModel"]
