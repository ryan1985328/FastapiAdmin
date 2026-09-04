
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema

from .constants import ProductStatus


class ProductCreateSchema(BaseModel):
    """Product reference record creation payload."""

    name: str = Field(..., min_length=1, max_length=128, description='名称')
    code: str = Field(..., min_length=1, max_length=64, description='编码')
    description: str | None = Field(default=None, max_length=2000, description='描述')
    image_url: str | None = Field(default=None, max_length=512, description='图片或存储标识')
    price: Decimal = Field(default=Decimal('0.00'), ge=Decimal('0'), max_digits=12, decimal_places=2, description='价格')
    stock: int = Field(default=0, ge=0, description='库存')
    status: int = Field(default=ProductStatus.OFF_SALE, ge=0, le=1, description='销售状态(0上架 1下架)')
    sort: int = Field(default=0, ge=0, description='排序')
    remark: str | None = Field(default=None, max_length=255, description='备注')

    @field_validator('name', 'code')
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('名称和编码不能为空')
        return value


class ProductUpdateSchema(BaseModel):
    """Product reference record partial update payload."""

    name: str | None = Field(default=None, min_length=1, max_length=128, description='名称')
    code: str | None = Field(default=None, min_length=1, max_length=64, description='编码')
    description: str | None = Field(default=None, max_length=2000, description='描述')
    image_url: str | None = Field(default=None, max_length=512, description='图片或存储标识')
    price: Decimal | None = Field(default=None, ge=Decimal('0'), max_digits=12, decimal_places=2, description='价格')
    stock: int | None = Field(default=None, ge=0, description='库存')
    status: int | None = Field(default=None, ge=0, le=1, description='销售状态(0上架 1下架)')
    sort: int | None = Field(default=None, ge=0, description='排序')
    remark: str | None = Field(default=None, max_length=255, description='备注')

    @field_validator('name', 'code')
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError('名称和编码不能为空')
        return value


class ProductOutSchema(ProductCreateSchema, BaseSchema, UserBySchema):
    """Product reference record response."""

    model_config = ConfigDict(from_attributes=True)


class ProductQueryParam(BaseQueryParam, UserByQueryParam):
    """Product list filters."""

    name: str | None = Field(None, description="名称", json_schema_extra={"q": "like"})
    code: str | None = Field(None, description="编码", json_schema_extra={"q": "like"})
    status: int | None = Field(None, ge=0, le=1, description="销售状态(0上架 1下架)", json_schema_extra={"q": "eq"})
