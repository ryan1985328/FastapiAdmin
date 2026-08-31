# -*- coding: utf-8 -*-


from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.core.base_schema import BaseSchema, UserBySchema, BaseQueryParam, UserByQueryParam
from app.core.validator import DateTimeStr
class AppUserKycCreateSchema(BaseModel):
    """
    用户实名认证新增模型
    """
    app_user_id: int = Field(default=..., description='用户端用户ID')
    real_name: str = Field(default=..., description='真实姓名')
    id_card_no: str = Field(default=..., description='证件号码')
    id_card_front: str | None = Field(default=None, description='证件正面地址')
    id_card_back: str | None = Field(default=None, description='证件反面地址')
    status: int = Field(default=0, ge=0, le=1, description='状态(0待审核 1通过 2拒绝)')
    review_remark: str | None = Field(default=None, description='审核备注')
    reviewed_at: DateTimeStr | None = Field(default=None, description='审核时间')


class AppUserKycUpdateSchema(BaseModel):
    """
    用户实名认证更新模型
    """
    app_user_id: int | None = Field(default=None, description='用户端用户ID')
    real_name: str | None = Field(default=None, description='真实姓名')
    id_card_no: str | None = Field(default=None, description='证件号码')
    id_card_front: str | None = Field(default=None, description='证件正面地址')
    id_card_back: str | None = Field(default=None, description='证件反面地址')
    status: int | None = Field(default=None, ge=0, le=1, description='状态(0待审核 1通过 2拒绝)')
    review_remark: str | None = Field(default=None, description='审核备注')
    reviewed_at: DateTimeStr | None = Field(default=None, description='审核时间')


class AppUserKycOutSchema(AppUserKycCreateSchema, BaseSchema, UserBySchema):
    """
    用户实名认证响应模型
    """
    model_config = ConfigDict(from_attributes=True)


class AppUserKycQueryParam(BaseQueryParam, UserByQueryParam):
    """用户实名认证查询参数"""

    app_user_id: int | None = Field(None, description="用户端用户ID", json_schema_extra={"q": "eq"})
    real_name: str | None = Field(None, description="真实姓名", json_schema_extra={"q": "like"})
    id_card_no: str | None = Field(None, description="证件号码", json_schema_extra={"q": "like"})
    id_card_front: str | None = Field(None, description="证件正面地址", json_schema_extra={"q": "like"})
    id_card_back: str | None = Field(None, description="证件反面地址", json_schema_extra={"q": "like"})
    status: int | None = Field(None, description="状态(0待审核 1通过 2拒绝)", json_schema_extra={"q": "eq"})
    review_remark: str | None = Field(None, description="审核备注", json_schema_extra={"q": "like"})
    reviewed_at: datetime | None = Field(None, description="审核时间", json_schema_extra={"q": "eq"})
