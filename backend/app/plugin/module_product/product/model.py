
from decimal import Decimal

from sqlalchemy import DECIMAL, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class ProductModel(ModelMixin, UserMixin):
    """Product reference table."""

    __tablename__: str = 'product'
    __table_args__: dict[str, str] = {'comment': '通用产品示例'}
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment='名称')
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True, comment='编码')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='描述')
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment='图片或存储标识')
    price: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, default=Decimal('0.00'), comment='价格')
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='库存')
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True, comment='状态(0启用 1停用)')
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='排序')
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='备注')
