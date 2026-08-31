"""Shared direct-referrer rules for App registration and Admin binding."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CustomException

from .model import AppUserModel
from .referral import normalize_referral_code


class AppUserReferralService:
    """Own the one-time direct-referrer binding contract."""

    @classmethod
    async def bind_by_code(
        cls,
        db: AsyncSession,
        *,
        user_id: int,
        referral_code: str,
    ) -> AppUserModel:
        try:
            normalized_code = normalize_referral_code(referral_code)
        except ValueError as exc:
            raise CustomException(msg="推荐码格式无效", status_code=422) from exc

        result = await db.execute(
            select(AppUserModel)
            .where(AppUserModel.id == user_id, AppUserModel.is_deleted.is_(False))
            .with_for_update()
        )
        user = result.scalars().first()
        if not user:
            raise CustomException(msg="绑定推荐人失败，该用户不存在")
        if user.referrer_id is not None:
            raise CustomException(msg="该用户已绑定推荐人，不允许重复绑定", status_code=409)

        referrer_result = await db.execute(
            select(AppUserModel).where(
                AppUserModel.referral_code == normalized_code,
                AppUserModel.is_deleted.is_(False),
            )
        )
        referrer = referrer_result.scalars().first()
        if not referrer:
            raise CustomException(msg="推荐码不存在或推荐人已删除")
        if referrer.id == user_id:
            raise CustomException(msg="不能绑定自己为推荐人", status_code=409)

        await cls.ensure_no_cycle(db, user_id=user_id, referrer_id=referrer.id)
        user.referrer_id = referrer.id
        user.referrer_bound_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def ensure_no_cycle(db: AsyncSession, *, user_id: int, referrer_id: int) -> None:
        """Walk the direct-referrer chain and reject self/repeated ancestors."""

        visited: set[int] = set()
        current_id: int | None = referrer_id
        while current_id is not None:
            if current_id == user_id:
                raise CustomException(msg="绑定推荐人会形成循环关系", status_code=409)
            if current_id in visited:
                raise CustomException(msg="推荐关系链已存在循环，无法继续绑定", status_code=409)
            visited.add(current_id)

            result = await db.execute(select(AppUserModel.referrer_id).where(AppUserModel.id == current_id))
            current_id = result.scalar_one_or_none()


__all__ = ["AppUserReferralService"]
