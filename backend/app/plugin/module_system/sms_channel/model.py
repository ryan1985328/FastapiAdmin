from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class SmsChannelModel(ModelMixin, UserMixin):
    """短信供应商渠道配置。``access_key_secret`` 只保存 Fernet 密文。"""

    __tablename__: str = "sms_channel"
    __table_args__: dict[str, str | bool] = {"comment": "短信渠道", "extend_existing": True}

    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="渠道名称")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, comment="供应商")
    access_key_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="AccessKey ID")
    access_key_secret: Mapped[str] = mapped_column(Text, nullable=False, comment="AccessKey Secret（密文）")
    sign_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="短信签名")
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment="状态（0启用 1停用）")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="是否默认渠道")
