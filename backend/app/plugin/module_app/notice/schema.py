from pydantic import BaseModel, ConfigDict, Field

from app.core.validator import DateTimeStr


class AppNoticeListItemSchema(BaseModel):
    """Public fields returned in the App notice list."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="公告ID")
    notice_title: str = Field(description="公告标题")
    notice_type: str = Field(description="公告类型")
    description: str | None = Field(default=None, description="公告摘要")
    created_time: DateTimeStr | None = Field(default=None, description="发布时间")


class AppNoticeDetailSchema(AppNoticeListItemSchema):
    """Public notice detail without Admin audit or technical fields."""

    notice_content: str | None = Field(default=None, description="公告正文")


__all__ = ["AppNoticeDetailSchema", "AppNoticeListItemSchema"]
