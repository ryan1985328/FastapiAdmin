from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class SmsLogModel(ModelMixin, UserMixin):
    """短信发送结果日志；不包含验证码字段。"""

    __tablename__: str = "sms_log"
    __table_args__: dict[str, str | bool] = {"comment": "短信记录", "extend_existing": True}

    mobile: Mapped[str] = mapped_column(String(32), nullable=False, comment="收件手机号")
    scene: Mapped[str] = mapped_column(String(64), nullable=False, comment="业务场景")
    template_code: Mapped[str] = mapped_column(String(128), nullable=False, comment="供应商模板编码")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, comment="供应商")
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment="状态（0成功 1失败）")
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="供应商请求ID")
    provider_code: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="供应商返回码")
    provider_message: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="供应商返回消息")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="发送时间")
