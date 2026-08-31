"""Business User summary projection helpers."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.plugin.module_system.kyc.model import AppUserKycModel

from .constants import AppUserKycStatus, aggregate_kyc_status
from .model import AppUserModel
from .schema import AppUserOutSchema, AppUserReferrerSummarySchema


async def get_latest_kyc(db: AsyncSession, app_user_id: int) -> AppUserKycModel | None:
    """Return the current non-deleted KYC record used for the summary.

    The App KYC flow maintains one logical active record. Ordering by the
    record id keeps the summary deterministic even if old data contains more
    than one active record; the existing KYC owner remains responsible for
    resolving that data-quality issue.
    """

    result = await db.execute(
        select(AppUserKycModel)
        .where(
            AppUserKycModel.app_user_id == app_user_id,
            AppUserKycModel.is_deleted.is_(False),
        )
        .order_by(AppUserKycModel.id.desc())
        .limit(1)
    )
    return result.scalars().first()


def to_referrer_summary(user: AppUserModel | None) -> AppUserReferrerSummarySchema | None:
    """Project a referrer without exposing credentials or full KYC data."""

    if user is None:
        return None
    return AppUserReferrerSummarySchema.model_validate(user)


def serialize_app_user(
    user: AppUserModel,
    *,
    referrer: AppUserModel | None = None,
    kyc_status: AppUserKycStatus = AppUserKycStatus.UNVERIFIED,
    kyc_reviewed_at: datetime | None = None,
) -> AppUserOutSchema:
    """Build the safe, computed Business User response from known projections."""

    return AppUserOutSchema.model_validate(
        {
            "id": user.id,
            "uuid": user.uuid,
            "created_time": user.created_time,
            "updated_time": user.updated_time,
            "is_deleted": user.is_deleted,
            "deleted_time": user.deleted_time,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "mobile": user.mobile,
            "status": user.status,
            "referral_code": user.referral_code,
            "referrer_id": user.referrer_id,
            "referrer_bound_at": user.referrer_bound_at,
            "referrer": to_referrer_summary(referrer),
            "has_referrer": user.referrer_id is not None,
            "kyc_status": kyc_status,
            "kyc_reviewed_at": kyc_reviewed_at,
        }
    )


async def get_app_user_out(db: AsyncSession, user: AppUserModel) -> AppUserOutSchema:
    """Load and serialize the direct referrer and KYC summary for one user."""

    referrer = None
    if user.referrer_id is not None:
        result = await db.execute(select(AppUserModel).where(AppUserModel.id == user.referrer_id))
        referrer = result.scalars().first()

    kyc = await get_latest_kyc(db, user.id)
    return serialize_app_user(
        user,
        referrer=referrer,
        kyc_status=aggregate_kyc_status(kyc.status if kyc else None),
        kyc_reviewed_at=kyc.reviewed_at if kyc else None,
    )


__all__ = ["get_app_user_out", "get_latest_kyc", "serialize_app_user", "to_referrer_summary"]
