from typing import Any

from sqlalchemy import String, cast, exists, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.plugin.module_app.bank_account.constants import (
    AppUserBankAccountStatus,
)
from app.plugin.module_app.bank_account.helpers import mask_card_number
from app.plugin.module_app.bank_account.model import AppUserBankAccountModel
from app.plugin.module_app.bank_account.schema import (
    AppUserBankAccountAdminOutSchema,
    AppUserBankAccountQueryParam,
    AppUserBankAccountUserSummarySchema,
)
from app.plugin.module_app.user.constants import AppUserKycStatus, aggregate_kyc_status
from app.plugin.module_app.user.model import AppUserModel
from app.plugin.module_system.kyc.model import AppUserKycModel
from app.utils.common_util import search_to_dict


class AppUserBankAccountService:
    """Admin read/status service; user self-service owns all card mutations."""

    _ORDERABLE_FIELDS = {"id", "created_time", "updated_time", "is_default", "status"}

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    @staticmethod
    def _latest_kyc_subquery():
        """Build the same latest non-deleted KYC projection used by App User."""

        kyc = aliased(AppUserKycModel)
        newer = aliased(AppUserKycModel)
        newer_exists = exists().where(
            newer.app_user_id == kyc.app_user_id,
            newer.is_deleted.is_(False),
            newer.id > kyc.id,
        )
        return (
            select(
                kyc.app_user_id.label("app_user_id"),
                kyc.status.label("status"),
                kyc.reviewed_at.label("reviewed_at"),
            )
            .where(kyc.is_deleted.is_(False), ~newer_exists)
            .subquery("latest_bank_account_kyc")
        )

    @classmethod
    def _order_columns(cls, order_by: list[dict[str, str]] | None) -> list[Any]:
        if not order_by:
            return [
                AppUserBankAccountModel.is_default.desc(),
                AppUserBankAccountModel.created_time.desc(),
                AppUserBankAccountModel.id.desc(),
            ]

        columns: list[Any] = []
        for item in order_by:
            for field, direction in item.items():
                if field not in cls._ORDERABLE_FIELDS:
                    continue
                column = getattr(AppUserBankAccountModel, field)
                columns.append(column.desc() if direction.lower() == "desc" else column.asc())
        return columns or [AppUserBankAccountModel.created_time.desc(), AppUserBankAccountModel.id.desc()]

    @classmethod
    def _conditions(cls, search: AppUserBankAccountQueryParam | None, latest_kyc: Any) -> list[Any]:
        conditions: list[Any] = [AppUserBankAccountModel.is_deleted.is_(False)]
        values = search_to_dict(search, {}) or {}

        for key, condition in values.items():
            if not isinstance(condition, tuple):
                continue
            operator, value = condition
            if value is None or value == "":
                continue

            if key == "keyword" and operator == "like":
                term = f"%{str(value).strip()}%"
                conditions.append(
                    or_(
                        cast(AppUserBankAccountModel.user_id, String).like(term),
                        AppUserModel.username.like(term),
                        AppUserModel.nickname.like(term),
                        AppUserModel.mobile.like(term),
                        AppUserBankAccountModel.account_name.like(term),
                        AppUserBankAccountModel.bank_name.like(term),
                        AppUserBankAccountModel.card_last4.like(term),
                    )
                )
            elif key == "user_id" and operator == "eq":
                conditions.append(AppUserBankAccountModel.user_id == value)
            elif key in {"bank_name", "account_name", "branch_name"} and operator == "like":
                conditions.append(getattr(AppUserBankAccountModel, key).like(f"%{value}%"))
            elif key == "is_default" and operator == "eq":
                conditions.append(AppUserBankAccountModel.is_default == bool(value))
            elif key == "status" and operator == "eq":
                conditions.append(AppUserBankAccountModel.status == int(value))
            elif key == "kyc_status" and operator == "eq":
                try:
                    kyc_status = AppUserKycStatus(str(value))
                except ValueError:
                    continue
                if kyc_status == AppUserKycStatus.UNVERIFIED:
                    conditions.append(latest_kyc.c.status.is_(None))
                else:
                    status_by_summary = {
                        AppUserKycStatus.PENDING: 0,
                        AppUserKycStatus.VERIFIED: 1,
                        AppUserKycStatus.REJECTED: 2,
                    }
                    conditions.append(latest_kyc.c.status == status_by_summary[kyc_status])
            elif key in {"created_time", "updated_time"} and operator == "between":
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    conditions.append(getattr(AppUserBankAccountModel, key).between(value[0], value[1]))

        return conditions

    @staticmethod
    def _serialize(
        account: AppUserBankAccountModel,
        user: AppUserModel | None,
        kyc_status: int | None,
    ) -> AppUserBankAccountAdminOutSchema:
        user_summary = None
        if user is not None:
            user_summary = AppUserBankAccountUserSummarySchema.model_validate(
                {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "mobile": user.mobile,
                    "kyc_status": aggregate_kyc_status(kyc_status),
                }
            )
        return AppUserBankAccountAdminOutSchema.model_validate(
            {
                "id": account.id,
                "uuid": account.uuid,
                "created_time": account.created_time,
                "updated_time": account.updated_time,
                "is_deleted": account.is_deleted,
                "deleted_time": account.deleted_time,
                "user_id": account.user_id,
                "bank_name": account.bank_name,
                "bank_code": account.bank_code,
                "account_name": account.account_name,
                "masked_card_number": mask_card_number(account.card_last4),
                "branch_name": account.branch_name,
                "is_default": bool(account.is_default),
                "status": AppUserBankAccountStatus(account.status),
                "app_user": user_summary,
            }
        )

    async def _fetch_one(
        self,
        account_id: int,
        *,
        lock: bool = False,
    ) -> tuple[AppUserBankAccountModel, AppUserModel | None, int | None] | None:
        latest_kyc = self._latest_kyc_subquery()
        from_clause = (
            AppUserBankAccountModel.__table__
            .outerjoin(AppUserModel.__table__, AppUserBankAccountModel.user_id == AppUserModel.id)
            .outerjoin(latest_kyc, AppUserModel.id == latest_kyc.c.app_user_id)
        )
        query = (
            select(AppUserBankAccountModel, AppUserModel, latest_kyc.c.status)
            .select_from(from_clause)
            .where(
                AppUserBankAccountModel.id == account_id,
                AppUserBankAccountModel.is_deleted.is_(False),
            )
        )
        if lock:
            query = query.with_for_update()
        result = await self.db.execute(query)
        return result.first()

    async def _fetch_rows(
        self,
        search: AppUserBankAccountQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> tuple[int, list[tuple[AppUserBankAccountModel, AppUserModel | None, int | None]]]:
        latest_kyc = self._latest_kyc_subquery()
        conditions = self._conditions(search, latest_kyc)
        from_clause = (
            AppUserBankAccountModel.__table__
            .outerjoin(AppUserModel.__table__, AppUserBankAccountModel.user_id == AppUserModel.id)
            .outerjoin(latest_kyc, AppUserModel.id == latest_kyc.c.app_user_id)
        )
        count_result = await self.db.execute(
            select(func.count(AppUserBankAccountModel.id)).select_from(from_clause).where(*conditions)
        )
        total = int(count_result.scalar() or 0)

        query = (
            select(AppUserBankAccountModel, AppUserModel, latest_kyc.c.status)
            .select_from(from_clause)
            .where(*conditions)
            .order_by(*self._order_columns(order_by))
        )
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        result = await self.db.execute(query)
        return total, result.all()

    async def detail(self, account_id: int) -> AppUserBankAccountAdminOutSchema:
        row = await self._fetch_one(account_id)
        if not row:
            raise CustomException(msg="该用户银行卡不存在", status_code=404)
        account, user, kyc_status = row
        return self._serialize(account, user, kyc_status)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: AppUserBankAccountQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[AppUserBankAccountAdminOutSchema]:
        offset = (page_no - 1) * page_size
        total, rows = await self._fetch_rows(search, order_by, offset, page_size)
        items = [self._serialize(account, user, kyc_status) for account, user, kyc_status in rows]
        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=offset + page_size < total,
            items=items,
        )

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

    async def change_status(self, account_id: int, action: str) -> AppUserBankAccountAdminOutSchema:
        if action not in {"enable", "disable"}:
            raise CustomException(msg="不支持的银行卡状态操作", status_code=422)

        current = await self._fetch_one(account_id)
        if not current:
            raise CustomException(msg="状态变更失败，该银行卡不存在", status_code=404)
        account_id_user = current[0].user_id
        await self._lock_user(account_id_user)
        locked = await self._fetch_one(account_id, lock=True)
        if not locked:
            raise CustomException(msg="状态变更失败，该银行卡不存在", status_code=404)
        account, _, _ = locked

        if action == "disable":
            was_default = bool(account.is_default)
            account.status = AppUserBankAccountStatus.DISABLED
            account.is_default = False
            if was_default:
                await self._replace_default(account.user_id, exclude_id=account.id)
        else:
            account.status = AppUserBankAccountStatus.ACTIVE
            if not await self._has_active_default(account.user_id, except_id=account.id):
                await self._clear_defaults(account.user_id, except_id=account.id)
                account.is_default = True

        await self.db.flush()
        refreshed = await self._fetch_one(account_id)
        if not refreshed:
            raise CustomException(msg="状态变更后银行卡不存在", status_code=404)
        return self._serialize(*refreshed)


__all__ = ["AppUserBankAccountService"]
