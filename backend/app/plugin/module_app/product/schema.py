from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import PageResultSchema


class AppProductImageSchema(BaseModel):
    """Public product image projection; native storage keys never leave App APIs."""

    url: str
    sort: int


class AppProductListItemSchema(BaseModel):
    """Safe public Product projection for the Mall list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cover_url: str | None = None
    images: list[AppProductImageSchema] = Field(default_factory=list)
    price: Decimal
    stock: int
    sold_out: bool


class AppProductDetailSchema(AppProductListItemSchema):
    description: str | None = None


class AppProductPageSchema(PageResultSchema[AppProductListItemSchema]):
    pass


__all__ = ["AppProductDetailSchema", "AppProductImageSchema", "AppProductListItemSchema", "AppProductPageSchema"]
