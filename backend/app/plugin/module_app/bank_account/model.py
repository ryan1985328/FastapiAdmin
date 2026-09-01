from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.core.base_model import ModelMixin


class AppUserBankAccountModel(ModelMixin):
    """App-owned bank account foundation.

    ``card_number`` is Fernet ciphertext.  Application code must use the
    explicit service/schema projection and never serialize this column.
    """

    __tablename__ = "app_user_bank_account"
    __table_args__ = (
        Index("ix_app_user_bank_account_user_default_deleted", "user_id", "is_default", "is_deleted"),
        Index("ix_app_user_bank_account_user_status_deleted", "user_id", "status", "is_deleted"),
        Index("ix_app_user_bank_account_user_created_deleted", "user_id", "created_time", "is_deleted"),
        {"comment": "用户银行卡"},
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("app_user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="App用户ID",
    )
    bank_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="银行名称")
    bank_code: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="银行代码")
    account_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="持卡人姓名")
    card_number: Mapped[str] = mapped_column(Text, nullable=False, comment="银行卡号密文")
    card_last4: Mapped[str] = mapped_column(String(4), nullable=False, comment="银行卡号末四位")
    branch_name: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="开户支行")
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="是否默认银行卡",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="状态(0正常 1禁用)",
    )


__all__ = ["AppUserBankAccountModel"]
