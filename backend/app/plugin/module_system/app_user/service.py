from datetime import UTC, datetime
from typing import Any

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.plugin.module_app.user.constants import AppUserKycStatus, AppUserStatus, aggregate_kyc_status
from app.plugin.module_app.user.model import AppUserModel
from app.plugin.module_app.user.schema import (
    AppUserBindReferrerSchema,
    AppUserOutSchema,
    AppUserStatusActionSchema,
)
from app.plugin.module_app.user.summary import get_app_user_out, serialize_app_user
from app.plugin.module_system.kyc.model import AppUserKycModel
from app.utils.common_util import search_to_dict
from app.utils.password_util import PwdUtil

from .crud import AppUserCRUD
from .schema import AppUserQueryParam, AppUserResetPasswordSchema, AppUserUpdateSchema


class AppUserService:
    """Admin management service for Business Users."""

    _STATUS_ACTION_TARGETS: dict[tuple[AppUserStatus, str], AppUserStatus] = {
        (AppUserStatus.ACTIVE, "disable"): AppUserStatus.DISABLED,
        (AppUserStatus.ACTIVE, "freeze"): AppUserStatus.FROZEN,
        (AppUserStatus.DISABLED, "enable"): AppUserStatus.ACTIVE,
        (AppUserStatus.FROZEN, "unfreeze"): AppUserStatus.ACTIVE,
    }
    _ORDERABLE_FIELDS = {
        "id",
        "username",
        "nickname",
        "mobile",
        "status",
        "referral_code",
        "created_time",
        "updated_time",
    }

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    @staticmethod
    def _latest_kyc_subquery():
        """Build a one-row-per-user projection from the existing KYC table."""

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
            .subquery("latest_app_user_kyc")
        )

    @classmethod
    def _conditions(
        cls,
        search: AppUserQueryParam | None,
        referrer: Any,
        latest_kyc: Any,
    ) -> list[Any]:
        conditions: list[Any] = [AppUserModel.is_deleted.is_(False)]
        values = search_to_dict(search, {}) or {}

        for key, condition in values.items():
            if not isinstance(condition, tuple):
                continue
            operator, value = condition
            if value is None:
                continue

            if key == "id":
                conditions.append(AppUserModel.id == value)
            elif key in {"username", "nickname", "mobile", "referral_code"}:
                conditions.append(getattr(AppUserModel, key).like(f"%{value}%"))
            elif key == "status":
                conditions.append(AppUserModel.status == int(value))
            elif key == "referrer":
                term = f"%{value}%"
                conditions.append(
                    or_(
                        referrer.username.like(term),
                        referrer.nickname.like(term),
                        referrer.mobile.like(term),
                        referrer.referral_code.like(term),
                    )
                )
            elif key == "kyc_status":
                try:
                    kyc_status = AppUserKycStatus(value)
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
                conditions.append(getattr(AppUserModel, key).between(value[0], value[1]))

        return conditions

    @classmethod
    def _order_columns(cls, order_by: list[dict[str, str]] | None) -> list[Any]:
        columns: list[Any] = []
        for item in order_by or []:
            for field, direction in item.items():
                if field not in cls._ORDERABLE_FIELDS:
                    continue
                column = getattr(AppUserModel, field)
                columns.append(column.desc() if direction.lower() == "desc" else column.asc())
        return columns or [AppUserModel.id.asc()]

    async def detail(self, id: int) -> AppUserOutSchema:
        obj = await AppUserCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return await get_app_user_out(self.db, obj)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: AppUserQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[AppUserOutSchema]:
        offset = (page_no - 1) * page_size
        referrer = aliased(AppUserModel)
        latest_kyc = self._latest_kyc_subquery()
        conditions = self._conditions(search, referrer, latest_kyc)

        from_clause = (
            AppUserModel.__table__
            .outerjoin(referrer, AppUserModel.referrer_id == referrer.id)
            .outerjoin(latest_kyc, AppUserModel.id == latest_kyc.c.app_user_id)
        )
        count_result = await self.db.execute(
            select(func.count(AppUserModel.id)).select_from(from_clause).where(*conditions)
        )
        total = count_result.scalar() or 0

        data_query = (
            select(AppUserModel, referrer, latest_kyc.c.status, latest_kyc.c.reviewed_at)
            .select_from(from_clause)
            .where(*conditions)
            .order_by(*self._order_columns(order_by))
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(data_query)
        items = [
            serialize_app_user(
                user,
                referrer=referrer_obj,
                kyc_status=aggregate_kyc_status(kyc_status),
                kyc_reviewed_at=reviewed_at,
            )
            for user, referrer_obj, kyc_status, reviewed_at in result.all()
        ]

        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=offset + page_size < total,
            items=items,
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
            await crud.update(id=id, data=update_data)
        refreshed = await crud.get(id=id)
        return await get_app_user_out(self.db, refreshed or obj)

    async def set_available(self, data: BatchSetAvailable) -> None:
        """Keep the legacy bulk 0/1 endpoint, while respecting FROZEN rules."""

        if not data.ids:
            raise CustomException(msg="状态变更失败，用户不能为空")

        target = AppUserStatus(data.status)
        crud = AppUserCRUD(self.auth, self.db)
        users = await crud.get_list(search={"id": ("in", data.ids)})
        if len(users) != len(set(data.ids)):
            raise CustomException(msg="状态变更失败，部分用户不存在")

        for user in users:
            current = AppUserStatus(user.status)
            if current == target:
                continue
            action = "disable" if target == AppUserStatus.DISABLED else "enable"
            if (current, action) not in self._STATUS_ACTION_TARGETS:
                raise CustomException(msg="状态变更不符合用户当前状态，请使用合法操作", status_code=409)

        for user in users:
            user.status = target
        await self.db.flush()

    async def change_status(self, id: int, data: AppUserStatusActionSchema) -> AppUserOutSchema:
        action = data.action
        if action not in {"enable", "disable", "freeze", "unfreeze"}:
            raise CustomException(msg="不支持的用户状态操作", status_code=422)

        result = await self.db.execute(
            select(AppUserModel)
            .where(AppUserModel.id == id, AppUserModel.is_deleted.is_(False))
            .with_for_update()
        )
        user = result.scalars().first()
        if not user:
            raise CustomException(msg="状态变更失败，该用户不存在")

        current = AppUserStatus(user.status)
        target = self._STATUS_ACTION_TARGETS.get((current, action))
        if target is None:
            raise CustomException(msg="状态变更不符合用户当前状态", status_code=409)

        user.status = target
        await self.db.flush()
        await self.db.refresh(user)
        return await get_app_user_out(self.db, user)

    async def reset_password(self, id: int, data: AppUserResetPasswordSchema) -> AppUserOutSchema:
        crud = AppUserCRUD(self.auth, self.db)
        user = await crud.get(id=id)
        if not user:
            raise CustomException(msg="重置密码失败，该用户不存在")

        password_hash = PwdUtil.hash_password(password=data.password)
        await crud.update(id=id, data={"password": password_hash})
        refreshed = await crud.get(id=id)
        return await get_app_user_out(self.db, refreshed or user)

    async def bind_referrer(self, id: int, data: AppUserBindReferrerSchema) -> AppUserOutSchema:
        result = await self.db.execute(
            select(AppUserModel)
            .where(AppUserModel.id == id, AppUserModel.is_deleted.is_(False))
            .with_for_update()
        )
        user = result.scalars().first()
        if not user:
            raise CustomException(msg="绑定推荐人失败，该用户不存在")
        if user.referrer_id is not None:
            raise CustomException(msg="该用户已绑定推荐人，不允许重复绑定", status_code=409)

        referrer_result = await self.db.execute(
            select(AppUserModel)
            .where(
                AppUserModel.referral_code == data.referral_code,
                AppUserModel.is_deleted.is_(False),
            )
        )
        referrer = referrer_result.scalars().first()
        if not referrer:
            raise CustomException(msg="推荐码不存在或推荐人已删除")
        if referrer.id == id:
            raise CustomException(msg="不能绑定自己为推荐人", status_code=409)

        await self._ensure_no_referral_cycle(user_id=id, referrer_id=referrer.id)
        user.referrer_id = referrer.id
        user.referrer_bound_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(user)
        return await get_app_user_out(self.db, user)

    async def _ensure_no_referral_cycle(self, *, user_id: int, referrer_id: int) -> None:
        """Walk the direct-referrer chain and reject self/repeated ancestors."""

        visited: set[int] = set()
        current_id: int | None = referrer_id
        while current_id is not None:
            if current_id == user_id:
                raise CustomException(msg="绑定推荐人会形成循环关系", status_code=409)
            if current_id in visited:
                raise CustomException(msg="推荐关系链已存在循环，无法继续绑定", status_code=409)
            visited.add(current_id)

            result = await self.db.execute(
                select(AppUserModel.referrer_id).where(AppUserModel.id == current_id)
            )
            current_id = result.scalar_one_or_none()


__all__ = ["AppUserService"]
