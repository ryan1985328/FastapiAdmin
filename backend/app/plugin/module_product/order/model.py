from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin

from .constants import ProductOrderStatus


class ProductOrderModel(ModelMixin):
    """A minimal Mall order aggregate with one or more immutable snapshots."""

    __tablename__ = "product_order"
    __table_args__ = (
        Index("ix_product_order_user_status_deleted", "user_id", "status", "is_deleted"),
        Index("ix_product_order_user_created_deleted", "user_id", "created_time", "is_deleted"),
        {"comment": "商城订单"},
    )

    order_no: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True, comment="订单号")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("app_user.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="App用户ID",
    )
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, comment="订单总金额")
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProductOrderStatus.PENDING_PAYMENT.value,
        index=True,
        comment="订单状态(PENDING_PAYMENT/PAID/CANCELLED)",
    )
    paid_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="支付时间")
    cancelled_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="取消时间")

    items: Mapped[list["ProductOrderItemModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="ProductOrderItemModel.id",
    )


class ProductOrderItemModel(ModelMixin):
    """Order line whose product-facing values are immutable snapshots."""

    __tablename__ = "product_order_item"
    __table_args__ = (
        Index("ix_product_order_item_order_deleted", "order_id", "is_deleted"),
        Index("ix_product_order_item_product_deleted", "product_id", "is_deleted"),
        {"comment": "商城订单商品快照"},
    )

    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_order.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="订单ID",
    )
    product_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("product.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
        comment="商品ID(商品删除后置空)",
    )
    product_name_snapshot: Mapped[str] = mapped_column(String(128), nullable=False, comment="商品名称快照")
    product_cover_snapshot: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="商品封面快照")
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, comment="成交单价快照")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="购买数量")
    subtotal: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, comment="商品小计")

    order: Mapped[ProductOrderModel] = relationship(back_populates="items")


__all__ = ["ProductOrderItemModel", "ProductOrderModel"]
