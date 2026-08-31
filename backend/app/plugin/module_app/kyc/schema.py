
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseSchema, UploadResponseSchema
from app.core.validator import DateTimeStr


class AppKycSubmissionSchema(BaseModel):
    """当前 App 用户提交实名认证资料。用户身份由访问令牌决定。"""

    real_name: str = Field(..., min_length=1, max_length=128, description="真实姓名")
    id_card_no: str = Field(..., min_length=6, max_length=64, description="证件号码")
    id_card_front: str = Field(..., min_length=1, max_length=512, description="证件正面 Storage 引用")
    id_card_back: str = Field(..., min_length=1, max_length=512, description="证件反面 Storage 引用")


class AppKycOutSchema(BaseSchema):
    """App 用户可查看的当前实名认证记录。"""

    model_config = ConfigDict(from_attributes=True)

    app_user_id: int = Field(..., description="用户端用户ID")
    real_name: str | None = Field(default=None, description="真实姓名")
    id_card_no: str = Field(..., description="证件号码")
    id_card_front: str | None = Field(default=None, description="证件正面 Storage 引用")
    id_card_back: str | None = Field(default=None, description="证件反面 Storage 引用")
    status: Literal[0, 1, 2] = Field(..., description="状态(0待审核 1通过 2拒绝)")
    review_remark: str | None = Field(default=None, description="审核备注")
    reviewed_at: DateTimeStr | None = Field(default=None, description="审核时间")


AppKycImageSide = Literal["front", "back"]


__all__ = [
    "AppKycImageSide",
    "AppKycOutSchema",
    "AppKycSubmissionSchema",
    "UploadResponseSchema",
]
