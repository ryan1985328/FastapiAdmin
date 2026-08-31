"""SMS channel administration and secret handling."""

from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.core.encrypt import encrypt_password
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict

from ..sms.service import SmsService
from .crud import SmsChannelCRUD
from .model import SmsChannelModel
from .schema import (
    SmsChannelCreateSchema,
    SmsChannelOutSchema,
    SmsChannelQueryParam,
    SmsChannelUpdateSchema,
    SmsTestSendResultSchema,
    SmsTestSendSchema,
)


class SmsChannelService:
    """Manage enabled providers without exposing access-key secrets."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    @staticmethod
    def _to_out(obj: SmsChannelModel) -> SmsChannelOutSchema:
        result = SmsChannelOutSchema.model_validate(obj)
        result.has_secret = bool(obj.access_key_secret)
        return result

    def _crud(self) -> SmsChannelCRUD:
        return SmsChannelCRUD(self.auth, self.db)

    async def _clear_other_defaults(self, keep_id: int) -> None:
        await self.db.execute(
            update(SmsChannelModel)
            .where(
                SmsChannelModel.id != keep_id,
                SmsChannelModel.is_deleted.is_(False),
                SmsChannelModel.is_default.is_(True),
            )
            .values(is_default=False),
        )
        await self.db.flush()

    async def detail(self, id: int) -> SmsChannelOutSchema:
        return self._to_out(await self._crud().get_or_404(id=id))

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: SmsChannelQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[SmsChannelOutSchema]:
        result = await self._crud().page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
        )
        return PageResultSchema[SmsChannelOutSchema](
            page_no=result.page_no,
            page_size=result.page_size,
            total=result.total,
            has_next=result.has_next,
            items=[self._to_out(obj) for obj in result.items],
        )

    async def create(self, data: SmsChannelCreateSchema) -> SmsChannelOutSchema:
        if data.status == 1 and data.is_default:
            raise CustomException(msg="停用渠道不能设为默认渠道", status_code=422)
        if await self._crud().get(name=data.name):
            raise CustomException(msg="创建失败，渠道名称已存在", status_code=409)

        payload = data.model_dump()
        payload["access_key_secret"] = encrypt_password(payload["access_key_secret"])
        obj = await self._crud().create(data=payload)
        if obj.is_default:
            await self._clear_other_defaults(obj.id)
        return self._to_out(obj)

    async def update(self, id: int, data: SmsChannelUpdateSchema) -> SmsChannelOutSchema:
        obj = await self._crud().get_or_404(id=id, msg="更新失败，该渠道不存在")
        payload = data.model_dump(exclude_unset=True, exclude_none=True)

        if "name" in payload:
            existing = await self._crud().get(name=payload["name"])
            if existing and existing.id != id:
                raise CustomException(msg="更新失败，渠道名称已存在", status_code=409)

        effective_status = payload.get("status", obj.status)
        effective_default = payload.get("is_default", bool(obj.is_default))
        if effective_status == 1 and effective_default:
            raise CustomException(msg="停用渠道不能设为默认渠道", status_code=422)
        if effective_status == 1:
            payload["is_default"] = False

        if "access_key_secret" in payload:
            if payload["access_key_secret"]:
                payload["access_key_secret"] = encrypt_password(payload["access_key_secret"])
            else:
                payload.pop("access_key_secret")

        updated = await self._crud().update(id=id, data=payload)
        if updated.is_default:
            await self._clear_other_defaults(id)
        return self._to_out(updated)

    async def set_available(self, data: BatchSetAvailable) -> None:
        if not data.ids:
            raise CustomException(msg="请选择要修改状态的渠道", status_code=422)
        rows = await self._crud().get_list(search={"id": ("in", data.ids)})
        found = {row.id for row in rows}
        missing = [id_ for id_ in data.ids if id_ not in found]
        if missing:
            raise CustomException(msg="部分短信渠道不存在", status_code=404)
        values: dict[str, Any] = {"status": data.status}
        if data.status == 1:
            values["is_default"] = False
        await self.db.execute(update(SmsChannelModel).where(SmsChannelModel.id.in_(data.ids)).values(**values))
        await self.db.flush()

    async def set_default(self, id: int) -> SmsChannelOutSchema:
        obj = await self._crud().get_or_404(id=id, msg="该短信渠道不存在")
        if obj.status == 1:
            raise CustomException(msg="停用渠道不能设为默认渠道", status_code=422)
        await self.db.execute(update(SmsChannelModel).where(SmsChannelModel.id != id).values(is_default=False))
        await self._crud().update(id=id, data={"is_default": True})
        return await self.detail(id)

    async def test_send(self, id: int, data: SmsTestSendSchema, redis) -> SmsTestSendResultSchema:
        result = await SmsService(self.db, redis, self.auth).test_send(
            mobile=data.mobile,
            scene=data.scene,
            params=data.params,
            channel_id=id,
        )
        return SmsTestSendResultSchema(
            provider=result.provider,
            success=result.success,
            code=result.code,
            message=result.message,
            request_id=result.request_id,
        )
