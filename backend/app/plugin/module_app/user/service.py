from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomException
from app.utils.password_util import PwdUtil

from .crud import AppUserCRUD
from .referral import generate_referral_code
from .schema import AppUserCreateSchema, AppUserOutSchema
from .summary import get_app_user_out


class AppUserService:
    """App user registration and safe profile operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.crud = AppUserCRUD(db)
        self.db = db

    async def _new_referral_code(self) -> str:
        """Generate a code and recheck the unique column before insertion."""

        for _ in range(10):
            referral_code = generate_referral_code()
            if not await self.crud.exists(include_deleted=True, referral_code=referral_code):
                return referral_code
        raise CustomException(msg="生成推荐码失败，请稍后重试", status_code=503)

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
                "referral_code": await self._new_referral_code(),
            },
        )
        return await self.to_out(user)

    async def get_by_username(self, username: str):
        return await self.crud.get_by_username(username)

    async def get_by_id(self, user_id: int):
        return await self.crud.get_by_id(user_id)

    async def to_out(self, user) -> AppUserOutSchema:
        """Return a safe user response with referral/KYC projections."""

        return await get_app_user_out(self.db, user)


__all__ = ["AppUserService"]
