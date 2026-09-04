
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseQueryParam, BaseSchema, UserByQueryParam, UserBySchema
from app.utils.xss_util import sanitize_html

from .constants import ProductStatus

PRODUCT_IMAGE_LIMIT = 9


class ProductImageInputSchema(BaseModel):
    """Native storage reference submitted by the protected Admin editor."""

    id: int | None = Field(default=None, ge=1, description="已有关联ID")
    storage_key: str = Field(..., min_length=1, max_length=512, description="存储对象key")
    source_id: int | None = Field(default=None, ge=1, description="存储源ID")
    sort: int = Field(default=0, ge=0, description="展示顺序")

    @field_validator("storage_key")
    @classmethod
    def validate_storage_key(cls, value: str) -> str:
        from app.api.v1.module_storage.file.public_media import normalize_public_storage_key

        try:
            return normalize_public_storage_key(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class ProductImageOutSchema(BaseModel):
    """Admin media response. ``storage_key`` is only used by the editor."""

    id: int | None = None
    storage_key: str | None = None
    source_id: int | None = None
    sort: int = 0
    url: str | None = None
    legacy: bool = False


class ProductCreateSchema(BaseModel):
    """Product reference record creation payload."""

    name: str = Field(..., min_length=1, max_length=128, description='名称')
    code: str = Field(..., min_length=1, max_length=64, description='编码')
    description: str | None = Field(default=None, max_length=65535, description='商品详情HTML')
    image_url: str | None = Field(default=None, max_length=512, description='图片或存储标识')
    price: Decimal = Field(default=Decimal('0.00'), ge=Decimal('0'), max_digits=12, decimal_places=2, description='价格')
    stock: int = Field(default=0, ge=0, description='库存')
    status: int = Field(default=ProductStatus.OFF_SALE, ge=0, le=1, description='销售状态(0上架 1下架)')
    sort: int = Field(default=0, ge=0, description='排序')
    remark: str | None = Field(default=None, max_length=255, description='备注')
    images: list[ProductImageInputSchema] = Field(default_factory=list, max_length=PRODUCT_IMAGE_LIMIT, description='商品图片')

    @field_validator('name', 'code')
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('名称和编码不能为空')
        return value

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, value: str | None) -> str | None:
        return sanitize_html(value) if value is not None else None

    @model_validator(mode="after")
    def validate_image_order(self):
        keys = [image.storage_key for image in self.images]
        if len(keys) != len(set(keys)):
            raise ValueError("商品图片不能重复")
        return self


class ProductUpdateSchema(BaseModel):
    """Product reference record partial update payload."""

    name: str | None = Field(default=None, min_length=1, max_length=128, description='名称')
    code: str | None = Field(default=None, min_length=1, max_length=64, description='编码')
    description: str | None = Field(default=None, max_length=65535, description='商品详情HTML')
    image_url: str | None = Field(default=None, max_length=512, description='图片或存储标识')
    price: Decimal | None = Field(default=None, ge=Decimal('0'), max_digits=12, decimal_places=2, description='价格')
    stock: int | None = Field(default=None, ge=0, description='库存')
    status: int | None = Field(default=None, ge=0, le=1, description='销售状态(0上架 1下架)')
    sort: int | None = Field(default=None, ge=0, description='排序')
    remark: str | None = Field(default=None, max_length=255, description='备注')
    images: list[ProductImageInputSchema] | None = Field(default=None, max_length=PRODUCT_IMAGE_LIMIT, description='商品图片')

    @field_validator('name', 'code')
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError('名称和编码不能为空')
        return value

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, value: str | None) -> str | None:
        return sanitize_html(value) if value is not None else None

    @model_validator(mode="after")
    def validate_image_order(self):
        if self.images is not None:
            keys = [image.storage_key for image in self.images]
            if len(keys) != len(set(keys)):
                raise ValueError("商品图片不能重复")
        return self


class ProductOutSchema(ProductCreateSchema, BaseSchema, UserBySchema):
    """Product reference record response."""

    model_config = ConfigDict(from_attributes=True)
    images: list[ProductImageOutSchema] = Field(default_factory=list, description='商品图片')
    cover_url: str | None = Field(default=None, description='当前主图访问地址')


class ProductQueryParam(BaseQueryParam, UserByQueryParam):
    """Product list filters."""

    name: str | None = Field(None, description="名称", json_schema_extra={"q": "like"})
    code: str | None = Field(None, description="编码", json_schema_extra={"q": "like"})
    status: int | None = Field(None, ge=0, le=1, description="销售状态(0上架 1下架)", json_schema_extra={"q": "eq"})
