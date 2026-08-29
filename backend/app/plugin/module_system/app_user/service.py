# -*- coding: utf-8 -*-

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.utils.common_util import search_to_dict
from app.utils.password_util import PwdUtil

from .crud import AppUserCRUD
from .schema import (
    AppUserOutSchema,
    AppUserQueryParam,
    AppUserResetPasswordSchema,
    AppUserUpdateSchema,
)


class AppUserService:
    """Admin management service for C-end users."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> AppUserOutSchema:
        obj = await AppUserCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return AppUserOutSchema.model_validate(obj)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: AppUserQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[AppUserOutSchema]:
        offset = (page_no - 1) * page_size
        return await AppUserCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search),
            out_schema=AppUserOutSchema,
        )

    async def update(self, id: int, data: AppUserUpdateSchema) -> AppUserOutSchema:
        crud = AppUserCRUD(self.auth, self.db)
        obj = await crud.get(id=id)
        if not obj:
            raise CustomException(msg="更新失败，该数据不存在")

        update_data = data.model_dump(exclude_unset=True)
        mobile = update_data.get("mobile")
        if mobile:
            existing = await crud.get(mobile=mobile)
            if existing and existing.id != id:
                raise CustomException(msg="更新失败，手机号重复")

        if update_data:
            obj = await crud.update(id=id, data=update_data)
        return AppUserOutSchema.model_validate(obj)

    async def set_available(self, data: BatchSetAvailable) -> None:
        if not data.ids:
            raise CustomException(msg="状态变更失败，用户不能为空")

        crud = AppUserCRUD(self.auth, self.db)
        users = await crud.get_list(search={"id": ("in", data.ids)})
        if len(users) != len(set(data.ids)):
            raise CustomException(msg="状态变更失败，部分用户不存在")
        await crud.set(ids=data.ids, status=data.status)

    async def reset_password(self, id: int, data: AppUserResetPasswordSchema) -> AppUserOutSchema:
        crud = AppUserCRUD(self.auth, self.db)
        user = await crud.get(id=id)
        if not user:
            raise CustomException(msg="重置密码失败，该用户不存在")

        password_hash = PwdUtil.hash_password(password=data.password)
        updated = await crud.update(id=id, data={"password": password_hash})
        return AppUserOutSchema.model_validate(updated)


__all__ = ["AppUserService"]
