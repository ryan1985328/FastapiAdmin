from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.core.encrypt import encrypt_password
from app.core.exceptions import CustomException

from ..user.model import AppUserModel
from .constants import AppUserBankAccountStatus
from .helpers import mask_card_number
from .model import AppUserBankAccountModel
from .schema import (
    AppUserBankAccountCreateSchema,
    AppUserBankAccountOutSchema,
    AppUserBankAccountUpdateSchema,
)


class AppUserBankAccountService:
    """Current App user's bank account service.

    User ownership, card encryption, and default-card invariants deliberately
    live together here, following the existing Address service pattern.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _lock_user(self, user_id: int) -> AppUserModel:
        result = await self.db.execute(
            select(AppUserModel)
            .where(AppUserModel.id == user_id, AppUserModel.is_deleted.is_(False))
            .with_for_update()
        )
        user = result.scalars().first()
        if not user:
            raise CustomException(msg="用户不存在", status_code=404)
        return user

    async def _get_owned(
        self,
        user_id: int,
        account_id: int,
        *,
        lock: bool = False,
    ) -> AppUserBankAccountModel:
        query = select(AppUserBankAccountModel).where(
            AppUserBankAccountModel.id == account_id,
            AppUserBankAccountModel.user_id == user_id,
            AppUserBankAccountModel.is_deleted.is_(False),
        )
        if lock:
            query = query.with_for_update()
        result = await self.db.execute(query)
        account = result.scalars().first()
        if not account:
            raise CustomException(msg="银行卡不存在", status_code=404)
        return account

    @staticmethod
    def _out(account: AppUserBankAccountModel) -> AppUserBankAccountOutSchema:
        return AppUserBankAccountOutSchema.model_validate(
            {
                "id": account.id,
                "bank_name": account.bank_name,
                "bank_code": account.bank_code,
                "account_name": account.account_name,
                "masked_card_number": mask_card_number(account.card_last4),
                "branch_name": account.branch_name,
                "is_default": bool(account.is_default),
                "status": AppUserBankAccountStatus(account.status),
            }
        )

    async def list(self, user_id: int) -> list[AppUserBankAccountOutSchema]:
        result = await self.db.execute(
            select(AppUserBankAccountModel)
            .where(
                AppUserBankAccountModel.user_id == user_id,
                AppUserBankAccountModel.is_deleted.is_(False),
            )
            .order_by(
                AppUserBankAccountModel.is_default.desc(),
                AppUserBankAccountModel.status.asc(),
                AppUserBankAccountModel.created_time.desc(),
                AppUserBankAccountModel.id.desc(),
            )
        )
        return [self._out(account) for account in result.scalars().all()]

    async def detail(self, user_id: int, account_id: int) -> AppUserBankAccountOutSchema:
        return self._out(await self._get_owned(user_id, account_id))

    async def _clear_defaults(self, user_id: int, *, except_id: int | None = None) -> None:
        query = (
            update(AppUserBankAccountModel)
            .where(
                AppUserBankAccountModel.user_id == user_id,
                AppUserBankAccountModel.is_deleted.is_(False),
                AppUserBankAccountModel.is_default.is_(True),
            )
            .values(is_default=False)
        )
        if except_id is not None:
            query = query.where(AppUserBankAccountModel.id != except_id)
        await self.db.execute(query)

    async def _has_active_default(self, user_id: int, *, except_id: int | None = None) -> bool:
        query = select(AppUserBankAccountModel.id).where(
            AppUserBankAccountModel.user_id == user_id,
            AppUserBankAccountModel.is_deleted.is_(False),
            AppUserBankAccountModel.status == AppUserBankAccountStatus.ACTIVE,
            AppUserBankAccountModel.is_default.is_(True),
        )
        if except_id is not None:
            query = query.where(AppUserBankAccountModel.id != except_id)
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def _replace_default(self, user_id: int, *, exclude_id: int | None = None) -> None:
        query = select(AppUserBankAccountModel).where(
            AppUserBankAccountModel.user_id == user_id,
            AppUserBankAccountModel.is_deleted.is_(False),
            AppUserBankAccountModel.status == AppUserBankAccountStatus.ACTIVE,
        )
        if exclude_id is not None:
            query = query.where(AppUserBankAccountModel.id != exclude_id)
        result = await self.db.execute(
            query
            .order_by(AppUserBankAccountModel.created_time.asc(), AppUserBankAccountModel.id.asc())
            .limit(1)
            .with_for_update()
        )
        replacement = result.scalars().first()
        if replacement:
            await self._clear_defaults(user_id, except_id=replacement.id)
            replacement.is_default = True

    async def create(
        self,
        user_id: int,
        data: AppUserBankAccountCreateSchema,
    ) -> AppUserBankAccountOutSchema:
        await self._lock_user(user_id)
        has_default = await self._has_active_default(user_id)
        is_default = bool(data.is_default) or not has_default
        if is_default:
            await self._clear_defaults(user_id)

        card_number = data.card_number
        account = AppUserBankAccountModel(
            user_id=user_id,
            bank_name=data.bank_name,
            bank_code=data.bank_code,
            account_name=data.account_name,
            card_number=encrypt_password(card_number),
            card_last4=card_number[-4:],
            branch_name=data.branch_name,
            is_default=is_default,
            status=AppUserBankAccountStatus.ACTIVE,
        )
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return self._out(account)

    async def update(
        self,
        user_id: int,
        account_id: int,
        data: AppUserBankAccountUpdateSchema,
    ) -> AppUserBankAccountOutSchema:
        await self._lock_user(user_id)
        account = await self._get_owned(user_id, account_id, lock=True)
        update_data: dict[str, Any] = data.model_dump(exclude_unset=True)
        requested_default = update_data.pop("is_default", None)

        if requested_default is True and account.status == AppUserBankAccountStatus.DISABLED:
            raise CustomException(msg="已禁用银行卡不能设为默认", status_code=409)

        card_number = update_data.pop("card_number", None)
        if card_number is not None:
            account.card_number = encrypt_password(card_number)
            account.card_last4 = card_number[-4:]

        for key, value in update_data.items():
            setattr(account, key, value)

        if requested_default is True:
            await self._clear_defaults(user_id, except_id=account.id)
            account.is_default = True
        elif requested_default is False and account.is_default:
            # Keep one valid default while the account remains active.
            account.is_default = account.status == AppUserBankAccountStatus.ACTIVE
            if not account.is_default:
                await self._replace_default(user_id, exclude_id=account.id)

        await self.db.flush()
        await self.db.refresh(account)
        return self._out(account)

    async def delete(self, user_id: int, account_id: int) -> None:
        await self._lock_user(user_id)
        account = await self._get_owned(user_id, account_id, lock=True)
        was_default = bool(account.is_default)
        account.is_deleted = True
        account.deleted_time = datetime.now(UTC)
        account.is_default = False

        if was_default:
            await self._replace_default(user_id, exclude_id=account.id)

        await self.db.flush()

    async def set_default(self, user_id: int, account_id: int) -> AppUserBankAccountOutSchema:
        await self._lock_user(user_id)
        account = await self._get_owned(user_id, account_id, lock=True)
        if account.status == AppUserBankAccountStatus.DISABLED:
            raise CustomException(msg="已禁用银行卡不能设为默认", status_code=409)
        await self._clear_defaults(user_id, except_id=account.id)
        account.is_default = True
        await self.db.flush()
        await self.db.refresh(account)
        return self._out(account)


__all__ = ["AppUserBankAccountService"]
