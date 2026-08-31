"""Read-only SMS send-log queries."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, PageResultSchema
from app.utils.common_util import search_to_dict

from ..sms.constants import mask_mobile
from .crud import SmsLogCRUD
from .model import SmsLogModel
from .schema import SmsLogOutSchema, SmsLogQueryParam


class SmsLogService:
    """Only the SMS service writes this table; Admin can query it."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    @staticmethod
    def _to_out(obj: SmsLogModel, *, mask: bool) -> SmsLogOutSchema:
        result = SmsLogOutSchema.model_validate(obj)
        if mask:
            result.mobile = mask_mobile(result.mobile)
        return result

    async def detail(self, id: int) -> SmsLogOutSchema:
        obj = await SmsLogCRUD(self.auth, self.db).get_or_404(id=id)
        return self._to_out(obj, mask=False)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: SmsLogQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[SmsLogOutSchema]:
        result = await SmsLogCRUD(self.auth, self.db).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "desc"}],
            search=search_to_dict(search),
        )
        return PageResultSchema[SmsLogOutSchema](
            page_no=result.page_no,
            page_size=result.page_size,
            total=result.total,
            has_next=result.has_next,
            items=[self._to_out(obj, mask=True) for obj in result.items],
        )
