from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.core.base_model import ModelMixin


class AppUserAddressModel(ModelMixin):
    """App 用户自服务地址。"""

    __tablename__ = "app_user_address"
    __table_args__ = (
        Index("ix_app_user_address_user_default_deleted", "user_id", "is_default", "is_deleted"),
        Index("ix_app_user_address_user_created_deleted", "user_id", "created_time", "is_deleted"),
        {"comment": "用户地址"},
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("app_user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="App用户ID",
    )
    receiver_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="收货人")
    receiver_mobile: Mapped[str] = mapped_column(String(32), nullable=False, comment="收货手机号")
    province: Mapped[str] = mapped_column(String(128), nullable=False, comment="省")
    city: Mapped[str] = mapped_column(String(128), nullable=False, comment="市")
    district: Mapped[str] = mapped_column(String(128), nullable=False, comment="区")
    detail_address: Mapped[str] = mapped_column(String(512), nullable=False, comment="详细地址")
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="邮政编码")
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="是否默认地址",
    )


__all__ = ["AppUserAddressModel"]
