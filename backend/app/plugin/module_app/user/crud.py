from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import AppUserModel
from .schema import AppUserCreateSchema


class AppUserCRUD(CRUDBase[AppUserModel, AppUserCreateSchema, AppUserCreateSchema]):
    """Data access for App users without admin audit/RBAC fields."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=AppUserModel, auth=AuthSchema(), db=db)

    async def get_by_username(self, username: str, *, include_deleted: bool = False) -> AppUserModel | None:
        return await self.get(username=username, include_deleted=include_deleted)

    async def get_by_id(self, user_id: int) -> AppUserModel | None:
        return await self.get(id=user_id)

    async def get_by_referral_code(self, referral_code: str, *, include_deleted: bool = False) -> AppUserModel | None:
        return await self.get(referral_code=referral_code, include_deleted=include_deleted)


__all__ = ["AppUserCRUD"]
