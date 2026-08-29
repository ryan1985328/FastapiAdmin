import json
import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.setting import settings
from app.core.base_schema import JWTOutSchema, JWTPayloadSchema
from app.core.exceptions import CustomException
from app.core.redis_crud import RedisCURD
from app.core.security import create_access_token, decode_access_token
from app.utils.password_util import PwdUtil

from ..user.model import AppUserModel
from ..user.schema import AppLoginOutSchema, AppLoginSchema, AppRefreshTokenSchema, AppUserOutSchema
from ..user.service import AppUserService
from .dependencies import (
    _access_token_key,
    _refresh_token_key,
    _session_key,
    parse_session,
)


class AppAuthService:
    """Token and session service for C-end users."""

    @classmethod
    async def login(cls, db: AsyncSession, redis: Redis, data: AppLoginSchema) -> AppLoginOutSchema:
        user = await AppUserService(db).get_by_username(data.username)
        if not user or not PwdUtil.verify_password(data.password, user.password):
            raise CustomException(msg="账号或密码错误", status_code=401, code=10401)
        if user.status == 1:
            raise CustomException(msg="用户已被停用", status_code=401, code=10401)

        token = await cls.issue_tokens(redis=redis, user=user)
        return AppLoginOutSchema(
            **token.model_dump(),
            user_info=AppUserOutSchema.model_validate(user),
        )

    @classmethod
    async def issue_tokens(
        cls,
        redis: Redis,
        user: AppUserModel,
        session_id: str | None = None,
    ) -> JWTOutSchema:
        session_id = session_id or str(uuid.uuid4())
        access_expires = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_expires = timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS)
        now = datetime.now(UTC)

        session_info = json.dumps(
            {
                "session_id": session_id,
                "user_id": user.id,
                "user_status": user.status,
                "username": user.username,
            },
            default=str,
        )
        await RedisCURD(redis).set(
            _session_key(session_id),
            session_info,
            expire=int(refresh_expires.total_seconds()),
        )

        access_token = create_access_token(
            JWTPayloadSchema(sub=session_id, is_refresh=False, exp=now + access_expires),
        )
        refresh_token = create_access_token(
            JWTPayloadSchema(sub=session_id, is_refresh=True, exp=now + refresh_expires),
        )
        await RedisCURD(redis).set(
            _access_token_key(session_id),
            access_token,
            expire=int(access_expires.total_seconds()),
        )
        await RedisCURD(redis).set(
            _refresh_token_key(session_id),
            refresh_token,
            expire=int(refresh_expires.total_seconds()),
        )

        return JWTOutSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=settings.TOKEN_TYPE,
            expires_in=int(access_expires.total_seconds()),
        )

    @classmethod
    async def refresh_token(cls, db: AsyncSession, redis: Redis, data: AppRefreshTokenSchema) -> JWTOutSchema:
        payload = decode_access_token(data.refresh_token)
        if not payload.is_refresh:
            raise CustomException(msg="非法凭证，请传入刷新令牌", status_code=401, code=10401)

        session_id = payload.sub
        session = parse_session(await RedisCURD(redis).get(_session_key(session_id)))
        user_id = session.get("user_id")
        if session.get("session_id") != session_id or not isinstance(user_id, int):
            raise CustomException(msg="会话已过期，请重新登录", status_code=401, code=10401)

        user = await AppUserService(db).get_by_id(user_id)
        if not user:
            raise CustomException(msg="刷新token失败，用户不存在", status_code=401, code=10401)
        if user.status == 1:
            raise CustomException(msg="用户已被停用", status_code=401, code=10401)
        return await cls.issue_tokens(redis=redis, user=user, session_id=session_id)

    @staticmethod
    async def logout(redis: Redis, token: str) -> bool:
        payload = decode_access_token(token, verify_exp=False)
        session_id = payload.sub
        if not session_id:
            raise CustomException(msg="非法凭证,无法获取会话编号", status_code=401, code=10401)
        await RedisCURD(redis).delete(
            _access_token_key(session_id),
            _refresh_token_key(session_id),
            _session_key(session_id),
        )
        return True


__all__ = ["AppAuthService"]
