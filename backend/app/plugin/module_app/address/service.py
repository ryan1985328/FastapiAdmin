from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomException
from app.utils.time_util import application_now

from ..user.model import AppUserModel
from .model import AppUserAddressModel
from .schema import AppUserAddressCreateSchema, AppUserAddressOutSchema, AppUserAddressUpdateSchema


class AppUserAddressService:
    """当前 App 用户地址服务，集中维护 ownership 和默认地址规则。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _lock_user(self, user_id: int) -> AppUserModel:
        result = await self.db.execute(select(AppUserModel).where(AppUserModel.id == user_id, AppUserModel.is_deleted.is_(False)).with_for_update())
        user = result.scalars().first()
        if not user:
            raise CustomException(msg="用户不存在", status_code=404)
        return user

    async def _get_owned(self, user_id: int, address_id: int, *, lock: bool = False) -> AppUserAddressModel:
        query = select(AppUserAddressModel).where(
            AppUserAddressModel.id == address_id,
            AppUserAddressModel.user_id == user_id,
            AppUserAddressModel.is_deleted.is_(False),
        )
        if lock:
            query = query.with_for_update()
        result = await self.db.execute(query)
        address = result.scalars().first()
        if not address:
            raise CustomException(msg="地址不存在", status_code=404)
        return address

    @staticmethod
    def _out(address: AppUserAddressModel) -> AppUserAddressOutSchema:
        return AppUserAddressOutSchema.model_validate(address)

    async def list(self, user_id: int) -> list[AppUserAddressOutSchema]:
        result = await self.db.execute(
            select(AppUserAddressModel)
            .where(
                AppUserAddressModel.user_id == user_id,
                AppUserAddressModel.is_deleted.is_(False),
            )
            .order_by(
                AppUserAddressModel.is_default.desc(),
                AppUserAddressModel.created_time.desc(),
                AppUserAddressModel.id.desc(),
            )
        )
        return [self._out(address) for address in result.scalars().all()]

    async def detail(self, user_id: int, address_id: int) -> AppUserAddressOutSchema:
        return self._out(await self._get_owned(user_id, address_id))

    async def _clear_defaults(self, user_id: int, *, except_id: int | None = None) -> None:
        query = (
            update(AppUserAddressModel)
            .where(
                AppUserAddressModel.user_id == user_id,
                AppUserAddressModel.is_deleted.is_(False),
                AppUserAddressModel.is_default.is_(True),
            )
            .values(is_default=False)
        )
        if except_id is not None:
            query = query.where(AppUserAddressModel.id != except_id)
        await self.db.execute(query)

    async def create(self, user_id: int, data: AppUserAddressCreateSchema) -> AppUserAddressOutSchema:
        await self._lock_user(user_id)
        result = await self.db.execute(
            select(AppUserAddressModel.id)
            .where(
                AppUserAddressModel.user_id == user_id,
                AppUserAddressModel.is_deleted.is_(False),
            )
            .limit(1)
        )
        has_existing = result.scalar_one_or_none() is not None
        is_default = data.is_default or not has_existing
        if is_default:
            await self._clear_defaults(user_id)

        address = AppUserAddressModel(
            user_id=user_id,
            **data.model_dump(exclude={"is_default"}),
            is_default=is_default,
        )
        self.db.add(address)
        await self.db.flush()
        await self.db.refresh(address)
        return self._out(address)

    async def update(
        self,
        user_id: int,
        address_id: int,
        data: AppUserAddressUpdateSchema,
    ) -> AppUserAddressOutSchema:
        await self._lock_user(user_id)
        address = await self._get_owned(user_id, address_id, lock=True)
        update_data: dict[str, Any] = data.model_dump(exclude_unset=True)
        requested_default = update_data.pop("is_default", None)

        for key, value in update_data.items():
            setattr(address, key, value)

        if requested_default is True:
            await self._clear_defaults(user_id, except_id=address.id)
            address.is_default = True
        elif requested_default is False and address.is_default:
            # 地址列表始终保留一个默认地址；编辑当前默认地址时不允许产生
            # “有地址但无默认地址”的中间状态。
            address.is_default = True

        await self.db.flush()
        await self.db.refresh(address)
        return self._out(address)

    async def delete(self, user_id: int, address_id: int) -> None:
        await self._lock_user(user_id)
        address = await self._get_owned(user_id, address_id, lock=True)
        was_default = bool(address.is_default)
        address.is_deleted = True
        address.deleted_time = application_now()
        address.is_default = False

        if was_default:
            result = await self.db.execute(
                select(AppUserAddressModel)
                .where(
                    AppUserAddressModel.user_id == user_id,
                    AppUserAddressModel.is_deleted.is_(False),
                    AppUserAddressModel.id != address.id,
                )
                .order_by(AppUserAddressModel.created_time.asc(), AppUserAddressModel.id.asc())
                .limit(1)
                .with_for_update()
            )
            replacement = result.scalars().first()
            if replacement:
                await self._clear_defaults(user_id, except_id=replacement.id)
                replacement.is_default = True

        await self.db.flush()

    async def set_default(self, user_id: int, address_id: int) -> AppUserAddressOutSchema:
        await self._lock_user(user_id)
        address = await self._get_owned(user_id, address_id, lock=True)
        await self._clear_defaults(user_id, except_id=address.id)
        address.is_default = True
        await self.db.flush()
        await self.db.refresh(address)
        return self._out(address)


__all__ = ["AppUserAddressService"]
