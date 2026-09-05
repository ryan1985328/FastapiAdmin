from typing import Any

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.plugin.module_app.address.model import AppUserAddressModel
from app.plugin.module_app.address.schema import (
    AppUserAddressAdminOutSchema,
    AppUserAddressQueryParam,
    AppUserAddressUserSummarySchema,
)
from app.plugin.module_app.user.model import AppUserModel
from app.utils.common_util import search_to_dict


class AppUserAddressService:
    """Admin 地址查询服务；地址自服务写操作不在 Admin 暴露。"""

    _ORDERABLE_FIELDS = {"id", "created_time", "updated_time", "is_default"}

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    @classmethod
    def _order_columns(cls, order_by: list[dict[str, str]] | None) -> list[Any]:
        if not order_by:
            return [
                AppUserAddressModel.is_default.desc(),
                AppUserAddressModel.created_time.desc(),
                AppUserAddressModel.id.desc(),
            ]

        columns: list[Any] = []
        for item in order_by:
            for field, direction in item.items():
                if field not in cls._ORDERABLE_FIELDS:
                    continue
                column = getattr(AppUserAddressModel, field)
                columns.append(column.desc() if direction.lower() == "desc" else column.asc())
        return columns or [AppUserAddressModel.created_time.desc(), AppUserAddressModel.id.desc()]

    @staticmethod
    def _serialize(
        address: AppUserAddressModel,
        user: AppUserModel | None,
    ) -> AppUserAddressAdminOutSchema:
        payload = AppUserAddressAdminOutSchema.model_validate(address).model_dump()
        payload["app_user"] = AppUserAddressUserSummarySchema.model_validate(user).model_dump() if user is not None else None
        return AppUserAddressAdminOutSchema.model_validate(payload)

    async def _conditions(self, search: AppUserAddressQueryParam | None) -> list[Any]:
        conditions: list[Any] = [AppUserAddressModel.is_deleted.is_(False)]
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
                        cast(AppUserAddressModel.user_id, String).like(term),
                        AppUserModel.username.like(term),
                        AppUserModel.nickname.like(term),
                        AppUserModel.mobile.like(term),
                        AppUserAddressModel.receiver_name.like(term),
                        AppUserAddressModel.receiver_mobile.like(term),
                    )
                )
            elif key == "is_default" and operator == "eq":
                conditions.append(AppUserAddressModel.is_default == bool(value))
            elif key == "user_id" and operator == "eq":
                conditions.append(AppUserAddressModel.user_id == value)
            elif key in {"province", "city", "district"} and operator == "like":
                conditions.append(getattr(AppUserAddressModel, key).like(f"%{value}%"))
            elif key in {"created_time", "updated_time"} and operator == "between":
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    conditions.append(getattr(AppUserAddressModel, key).between(value[0], value[1]))

        return conditions

    async def _fetch_rows(
        self,
        search: AppUserAddressQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> tuple[int, list[tuple[AppUserAddressModel, AppUserModel | None]]]:
        conditions = await self._conditions(search)
        from_clause = AppUserAddressModel.__table__.outerjoin(AppUserModel.__table__, AppUserAddressModel.user_id == AppUserModel.id)

        count_result = await self.db.execute(select(func.count(AppUserAddressModel.id)).select_from(from_clause).where(*conditions))
        total = int(count_result.scalar() or 0)

        query = select(AppUserAddressModel, AppUserModel).select_from(from_clause).where(*conditions).order_by(*self._order_columns(order_by))
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        result = await self.db.execute(query)
        return total, result.all()

    async def detail(self, address_id: int) -> AppUserAddressAdminOutSchema:
        conditions = [
            AppUserAddressModel.id == address_id,
            AppUserAddressModel.is_deleted.is_(False),
        ]
        from_clause = AppUserAddressModel.__table__.outerjoin(AppUserModel.__table__, AppUserAddressModel.user_id == AppUserModel.id)
        result = await self.db.execute(select(AppUserAddressModel, AppUserModel).select_from(from_clause).where(*conditions))
        row = result.first()
        if not row:
            raise CustomException(msg="该用户地址不存在", status_code=404)
        address, user = row
        return self._serialize(address, user)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: AppUserAddressQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[AppUserAddressAdminOutSchema]:
        offset = (page_no - 1) * page_size
        total, rows = await self._fetch_rows(
            search=search,
            order_by=order_by,
            offset=offset,
            limit=page_size,
        )
        items = [self._serialize(address, user) for address, user in rows]
        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=offset + page_size < total,
            items=items,
        )


__all__ = ["AppUserAddressService"]
