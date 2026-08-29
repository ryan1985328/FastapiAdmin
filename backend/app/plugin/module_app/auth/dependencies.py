import json

from fastapi import Depends
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import RET
from app.config.setting import settings
from app.core.dependencies import db_getter, redis_getter
from app.core.exceptions import CustomException
from app.core.redis_crud import RedisCURD
from app.core.security import CustomOAuth2PasswordBearer, decode_access_token

from ..user.crud import AppUserCRUD
from ..user.model import AppUserModel

APP_SESSION_PREFIX = "app_user_session"
APP_ACCESS_TOKEN_PREFIX = "app_access_token"
APP_REFRESH_TOKEN_PREFIX = "app_refresh_token"

AppOAuth2Schema = CustomOAuth2PasswordBearer(
    token_url="app/auth/login",
    description="C端用户认证",
)


def _session_key(session_id: str) -> str:
    return f"{APP_SESSION_PREFIX}:{session_id}"


def _access_token_key(session_id: str) -> str:
    return f"{APP_ACCESS_TOKEN_PREFIX}:{session_id}"


def _refresh_token_key(session_id: str) -> str:
    return f"{APP_REFRESH_TOKEN_PREFIX}:{session_id}"


def parse_session(raw: object) -> dict:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if not raw:
        return {}
    try:
        value = json.loads(str(raw))
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


async def get_current_app_user(
    db: AsyncSession = Depends(db_getter),
    redis: Redis = Depends(redis_getter),
    token: str = Depends(AppOAuth2Schema),
) -> AppUserModel:
    """Authenticate an App user without entering the admin Auth/RBAC path."""
    if not token:
        raise CustomException(msg="认证已失效", code=RET.UNAUTHORIZED.code, status_code=401)

    payload = decode_access_token(token, verify_exp=not settings.TOKEN_SLIDING_EXPIRE)
    if payload.is_refresh:
        raise CustomException(msg="非法凭证", code=RET.INVALID_CREDENTIALS.code, status_code=401)

    session_id = payload.sub
    session = parse_session(await RedisCURD(redis).get(_session_key(session_id)))
    if session.get("session_id") != session_id:
        raise CustomException(msg="认证已失效", code=RET.UNAUTHORIZED.code, status_code=401)

    user_id = session.get("user_id")
    if not isinstance(user_id, int):
        raise CustomException(msg="认证已失效", code=RET.UNAUTHORIZED.code, status_code=401)

    if settings.TOKEN_SLIDING_EXPIRE:
        ttl = await RedisCURD(redis).ttl(_session_key(session_id))
        if 0 < ttl < settings.ACCESS_TOKEN_EXPIRE_SECONDS // 2:
            await RedisCURD(redis).expire(_session_key(session_id), settings.REFRESH_TOKEN_EXPIRE_SECONDS)
            await RedisCURD(redis).expire(_access_token_key(session_id), settings.ACCESS_TOKEN_EXPIRE_SECONDS)
            await RedisCURD(redis).expire(_refresh_token_key(session_id), settings.REFRESH_TOKEN_EXPIRE_SECONDS)

    user = await AppUserCRUD(db).get_by_id(user_id)
    if not user:
        raise CustomException(msg="用户不存在", code=RET.NOT_FOUND.code, status_code=401)
    if user.status == 1:
        raise CustomException(msg="用户已被停用", code=RET.UNAUTHORIZED.code, status_code=401)
    return user


__all__ = [
    "APP_ACCESS_TOKEN_PREFIX",
    "APP_REFRESH_TOKEN_PREFIX",
    "APP_SESSION_PREFIX",
    "AppOAuth2Schema",
    "_access_token_key",
    "_refresh_token_key",
    "_session_key",
    "get_current_app_user",
    "parse_session",
]
