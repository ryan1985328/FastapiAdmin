from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomException
from app.plugin.module_system.sms.constants import normalize_mobile
from app.plugin.module_system.sms.service import SmsService
from app.utils.password_util import PwdUtil

from .crud import AppUserCRUD
from .referral import generate_referral_code
from .referral_service import AppUserReferralService
from .schema import AppUserCreateSchema, AppUserOutSchema, AppUserProfileUpdateSchema
from .summary import get_app_user_out


class AppUserService:
    """App user registration and safe profile operations."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None) -> None:
        self.crud = AppUserCRUD(db)
        self.db = db
        self.redis = redis

    async def _new_referral_code(self) -> str:
        """Generate a code and recheck the unique column before insertion."""

        for _ in range(10):
            referral_code = generate_referral_code()
            if not await self.crud.exists(include_deleted=True, referral_code=referral_code):
                return referral_code
        raise CustomException(msg="生成推荐码失败，请稍后重试", status_code=503)

    async def _new_internal_username(self) -> str:
        """Create a collision-resistant username for mobile-only accounts."""

        from uuid import uuid4

        for _ in range(10):
            username = f"mobile_{uuid4().hex}"
            if not await self.crud.get_by_username(username, include_deleted=True):
                return username
        raise CustomException(msg="生成用户标识失败，请稍后重试", status_code=503)

    async def register(self, data: AppUserCreateSchema) -> AppUserOutSchema:
        normalized_mobile = normalize_mobile(data.mobile) if data.mobile else None
        # A body without username is the new phone registration path. A body
        # with username and no code remains compatible with existing clients.
        mobile_registration = data.username is None or data.code is not None
        if mobile_registration:
            if not normalized_mobile or not data.code:
                raise CustomException(msg="手机号注册需要手机号和短信验证码", status_code=422)
            if await self.crud.get_by_mobile(normalized_mobile, include_deleted=True):
                raise CustomException(msg="该手机号已注册", status_code=409)
            if self.redis is None:
                raise CustomException(msg="短信认证服务不可用", status_code=503)
            await SmsService(self.db, self.redis).verify_code(
                mobile=normalized_mobile,
                scene="register_code",
                code=data.code,
            )

        username = data.username or await self._new_internal_username()
        if await self.crud.get_by_username(username, include_deleted=True):
            raise CustomException(msg="已存在相同用户名称的账号", status_code=409)

        user = await self.crud.create(
            {
                "username": username,
                "password": PwdUtil.hash_password(data.password),
                "nickname": data.nickname or normalized_mobile or username,
                "avatar": data.avatar,
                "mobile": normalized_mobile,
                "status": 0,
                "referral_code": await self._new_referral_code(),
            },
        )
        if data.referral_code:
            user = await AppUserReferralService.bind_by_code(
                self.db,
                user_id=user.id,
                referral_code=data.referral_code,
            )
        return await self.to_out(user)

    async def get_by_username(self, username: str):
        return await self.crud.get_by_username(username)

    async def get_by_id(self, user_id: int):
        return await self.crud.get_by_id(user_id)

    async def get_by_mobile(self, mobile: str, *, include_deleted: bool = False):
        return await self.crud.get_by_mobile(normalize_mobile(mobile), include_deleted=include_deleted)

    async def to_out(self, user) -> AppUserOutSchema:
        """Return a safe user response with referral/KYC projections."""

        return await get_app_user_out(self.db, user)

    async def update_profile(self, user, data: AppUserProfileUpdateSchema) -> AppUserOutSchema:
        """Update only the fields explicitly allowed in App self-service."""

        updated = await self.crud.update(id=user.id, data={"nickname": data.nickname})
        return await self.to_out(updated)


__all__ = ["AppUserService"]
