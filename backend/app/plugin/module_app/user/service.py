from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomException
from app.utils.password_util import PwdUtil

from .crud import AppUserCRUD
from .schema import AppUserCreateSchema, AppUserOutSchema


class AppUserService:
    """App user registration and safe profile operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.crud = AppUserCRUD(db)

    async def register(self, data: AppUserCreateSchema) -> AppUserOutSchema:
        if await self.crud.get_by_username(data.username, include_deleted=True):
            raise CustomException(msg="已存在相同用户名称的账号", status_code=409)

        user = await self.crud.create(
            {
                "username": data.username,
                "password": PwdUtil.hash_password(data.password),
                "nickname": data.nickname or data.username,
                "avatar": data.avatar,
                "mobile": data.mobile,
                "status": 0,
            },
        )
        return AppUserOutSchema.model_validate(user)

    async def get_by_username(self, username: str):
        return await self.crud.get_by_username(username)

    async def get_by_id(self, user_id: int):
        return await self.crud.get_by_id(user_id)


__all__ = ["AppUserService"]
