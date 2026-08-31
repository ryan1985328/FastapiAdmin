"""Read-only Admin schemas for SMS send logs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseQueryParam, BaseSchema
from app.core.validator import DateTimeStr


class SmsLogCreateSchema(BaseModel):
    """Internal-only shape retained for typing; no HTTP create route exists."""

    mobile: str
    scene: str
    template_code: str
    provider: str
    status: int = Field(default=0, ge=0, le=1)
    provider_request_id: str | None = None
    provider_code: str | None = None
    provider_message: str | None = None
    sent_at: datetime | None = None


class SmsLogUpdateSchema(BaseModel):
    """Internal-only shape retained for the generated CRUD type parameters."""

    mobile: str | None = None
    scene: str | None = None
    template_code: str | None = None
    provider: str | None = None
    status: int | None = Field(default=None, ge=0, le=1)
    provider_request_id: str | None = None
    provider_code: str | None = None
    provider_message: str | None = None
    sent_at: datetime | None = None


class SmsLogOutSchema(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    mobile: str
    scene: str
    template_code: str
    provider: str
    status: int
    provider_request_id: str | None = None
    provider_code: str | None = None
    provider_message: str | None = None
    sent_at: DateTimeStr | None = None


class SmsLogQueryParam(BaseQueryParam):
    mobile: str | None = Field(default=None, description="手机号", json_schema_extra={"q": "like"})
    scene: str | None = Field(default=None, description="业务场景", json_schema_extra={"q": "eq"})
    provider: str | None = Field(default=None, description="供应商", json_schema_extra={"q": "eq"})
    status: int | None = Field(default=None, ge=0, le=1, description="状态", json_schema_extra={"q": "eq"})


__all__ = ["SmsLogCreateSchema", "SmsLogOutSchema", "SmsLogQueryParam", "SmsLogUpdateSchema"]
