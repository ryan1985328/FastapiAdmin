from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.notice.model import NoticeModel
from app.common.enums import RET
from app.core.base_schema import PageResultSchema
from app.core.exceptions import CustomException

from .schema import AppNoticeDetailSchema, AppNoticeListItemSchema

PUBLIC_NOTICE_STATUS = 0


class AppNoticeService:
    """Read-only public projection of the existing system Notice table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _public_conditions():
        return [
            NoticeModel.is_deleted.is_(False),
            NoticeModel.status == PUBLIC_NOTICE_STATUS,
        ]

    async def page(self, page_no: int, page_size: int) -> PageResultSchema[AppNoticeListItemSchema]:
        conditions = self._public_conditions()
        total_result = await self.db.execute(
            select(func.count(NoticeModel.id)).where(*conditions),
        )
        total = total_result.scalar() or 0

        result = await self.db.execute(
            select(NoticeModel)
            .where(*conditions)
            .order_by(NoticeModel.created_time.desc(), NoticeModel.id.desc())
            .offset((page_no - 1) * page_size)
            .limit(page_size),
        )
        items = [AppNoticeListItemSchema.model_validate(item) for item in result.scalars().all()]
        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=page_no * page_size < total,
            items=items,
        )

    async def detail(self, notice_id: int) -> AppNoticeDetailSchema:
        result = await self.db.execute(
            select(NoticeModel).where(
                NoticeModel.id == notice_id,
                *self._public_conditions(),
            ),
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise CustomException(msg="公告不存在", code=RET.NOT_FOUND.code, status_code=404)
        return AppNoticeDetailSchema.model_validate(item)


__all__ = ["AppNoticeService", "PUBLIC_NOTICE_STATUS"]
