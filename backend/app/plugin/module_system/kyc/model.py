# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin

class AppUserKycModel(ModelMixin):
    """
    用户实名认证表
    """
    __tablename__: str = 'app_user_kyc'
    # Reuse an already reflected/declared Table when generating Admin CRUD for an existing model.
    __table_args__: dict[str, str | bool] = {'comment': '用户实名认证', 'extend_existing': True}
    app_user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='用户端用户ID')
    real_name: Mapped[str | None] = mapped_column(String(128), nullable=True, comment='真实姓名')
    id_card_no: Mapped[str] = mapped_column(String(64), nullable=False, comment='证件号码')
    id_card_front: Mapped[str | None] = mapped_column(String(512), nullable=True, comment='证件正面地址')
    id_card_back: Mapped[str | None] = mapped_column(String(512), nullable=True, comment='证件反面地址')
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment='状态(0待审核 1通过 2拒绝)')
    review_remark: Mapped[str | None] = mapped_column(String(512), nullable=True, comment='审核备注')
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='审核时间')
