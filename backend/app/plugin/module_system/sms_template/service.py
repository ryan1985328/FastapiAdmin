"""SMS template administration."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException

from .crud import SmsTemplateCRUD
from .model import SmsTemplateModel
from .schema import SmsTemplateCreateSchema, SmsTemplateOutSchema, SmsTemplateQueryParam, SmsTemplateUpdateSchema


class SmsTemplateService:
    """Keep business scenes independent from provider template codes."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    def _crud(self) -> SmsTemplateCRUD:
        return SmsTemplateCRUD(self.auth, self.db)

    async def _assert_unique(self, *, name: str, scene: str, provider: str, exclude_id: int | None = None) -> None:
        conditions = [SmsTemplateModel.is_deleted.is_(False)]
        if exclude_id is not None:
            conditions.append(SmsTemplateModel.id != exclude_id)
        duplicate = (
            (
                await self.db.execute(
                    select(SmsTemplateModel).where(
                        *conditions,
                        (SmsTemplateModel.name == name) | ((SmsTemplateModel.scene == scene) & (SmsTemplateModel.provider == provider)),
                    ),
                )
            )
            .scalars()
            .first()
        )
        if duplicate:
            if duplicate.name == name:
                raise CustomException(msg="模板名称已存在", status_code=409)
            raise CustomException(msg="同一场景与供应商只能配置一个模板", status_code=409)

    async def detail(self, id: int) -> SmsTemplateOutSchema:
        return SmsTemplateOutSchema.model_validate(await self._crud().get_or_404(id=id))

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: SmsTemplateQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[SmsTemplateOutSchema]:
        from app.utils.common_util import search_to_dict

        return await self._crud().page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            out_schema=SmsTemplateOutSchema,
        )

    async def create(self, data: SmsTemplateCreateSchema) -> SmsTemplateOutSchema:
        await self._assert_unique(name=data.name, scene=data.scene, provider=data.provider)
        obj = await self._crud().create(data=data)
        return SmsTemplateOutSchema.model_validate(obj)

    async def update(self, id: int, data: SmsTemplateUpdateSchema) -> SmsTemplateOutSchema:
        obj = await self._crud().get_or_404(id=id, msg="更新失败，该短信模板不存在")
        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        await self._assert_unique(
            name=payload.get("name", obj.name),
            scene=payload.get("scene", obj.scene),
            provider=payload.get("provider", obj.provider),
            exclude_id=id,
        )
        updated = await self._crud().update(id=id, data=payload)
        return SmsTemplateOutSchema.model_validate(updated)

    async def set_available(self, data: BatchSetAvailable) -> None:
        if not data.ids:
            raise CustomException(msg="请选择要修改状态的模板", status_code=422)
        rows = await self._crud().get_list(search={"id": ("in", data.ids)})
        if {row.id for row in rows} != set(data.ids):
            raise CustomException(msg="部分短信模板不存在", status_code=404)
        await self.db.execute(update(SmsTemplateModel).where(SmsTemplateModel.id.in_(data.ids)).values(status=data.status))
        await self.db.flush()
