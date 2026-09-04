
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin

from .constants import ProductStatus


class ProductImageModel(ModelMixin, UserMixin):
    """Ordered media association for a Product.

    Removing an association is a soft delete. The referenced storage object
    is intentionally never deleted as part of product editing.
    """

    __tablename__: str = "product_image"
    __table_args__: dict[str, str] = {"comment": "商品图片关联"}

    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="商品ID",
    )
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, comment="存储对象key")
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_source.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
        comment="存储源ID",
    )
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="展示顺序")

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
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=ProductStatus.OFF_SALE,
        index=True,
        comment='销售状态(0上架 1下架)',
    )
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='排序')
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='备注')
