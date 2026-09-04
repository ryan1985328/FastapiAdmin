from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseQueryParam, BaseSchema, PageResultSchema
from app.core.validator import DateTimeStr

from .constants import ProductOrderStatus


class AppOrderCreateSchema(BaseModel):
    """The client can select only a product and a bounded quantity."""

    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(..., ge=1, description="商品ID")
    quantity: int = Field(..., ge=1, le=999, description="购买数量")


class AppOrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None = None
    product_name: str
    product_cover: str | None = None
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class AppOrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    total_amount: Decimal
    status: ProductOrderStatus
    created_time: DateTimeStr | None = None
    updated_time: DateTimeStr | None = None
    paid_time: DateTimeStr | None = None
    cancelled_time: DateTimeStr | None = None
    items: list[AppOrderItemSchema] = Field(default_factory=list)


class AppOrderPageSchema(PageResultSchema[AppOrderSchema]):
    pass


class ProductOrderQueryParam(BaseQueryParam):
    keyword: str | None = Field(default=None, max_length=128, description="订单号、用户或商品关键词")
    status: ProductOrderStatus | None = Field(default=None, description="订单状态")
    user_id: int | None = Field(default=None, ge=1, description="App用户ID")


class ProductOrderAdminItemSchema(BaseSchema):
    order_no: str
    user_id: int
    username: str | None = None
    nickname: str | None = None
    mobile: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    quantity: int | None = None
    total_amount: Decimal
    status: ProductOrderStatus
    paid_time: DateTimeStr | None = None
    cancelled_time: DateTimeStr | None = None


class ProductOrderAdminItemDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None = None
    product_name: str
    product_cover: str | None = None
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class ProductOrderAdminDetailSchema(BaseSchema):
    user_id: int
    username: str | None = None
    nickname: str | None = None
    mobile: str | None = None
    order_no: str
    total_amount: Decimal
    status: ProductOrderStatus
    paid_time: DateTimeStr | None = None
    cancelled_time: DateTimeStr | None = None
    items: list[ProductOrderAdminItemDetailSchema] = Field(default_factory=list)


__all__ = [
    "AppOrderCreateSchema",
    "AppOrderItemSchema",
    "AppOrderPageSchema",
    "AppOrderSchema",
    "ProductOrderAdminDetailSchema",
    "ProductOrderAdminItemDetailSchema",
    "ProductOrderAdminItemSchema",
    "ProductOrderQueryParam",
    "ProductOrderStatus",
]
