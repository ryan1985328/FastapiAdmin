from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class SmsTemplateModel(ModelMixin, UserMixin):
    """业务场景到供应商模板编码的映射。"""

    __tablename__: str = "sms_template"
    __table_args__: dict[str, str | bool] = {"comment": "短信模板", "extend_existing": True}

    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="模板名称")
    scene: Mapped[str] = mapped_column(String(64), nullable=False, comment="业务场景")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, comment="供应商")
    provider_template_code: Mapped[str] = mapped_column(String(128), nullable=False, comment="供应商模板编码")
    param_schema: Mapped[list[str]] = mapped_column(JSON, nullable=False, comment="允许的模板参数名")
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment="状态（0启用 1停用）")
