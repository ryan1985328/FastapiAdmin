from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.base_schema import PageResultSchema


class AppProductListItemSchema(BaseModel):
    """Safe public Product projection for the Mall list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cover_url: str | None = None
    price: Decimal
    stock: int
    sold_out: bool


class AppProductDetailSchema(AppProductListItemSchema):
    description: str | None = None


class AppProductPageSchema(PageResultSchema[AppProductListItemSchema]):
    pass


__all__ = ["AppProductDetailSchema", "AppProductListItemSchema", "AppProductPageSchema"]
