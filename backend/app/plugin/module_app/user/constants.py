"""Shared Business User status and summary constants."""

from enum import IntEnum, StrEnum


class AppUserStatus(IntEnum):
    """Business status values for ``app_user``.

    ``ACTIVE`` and ``DISABLED`` preserve the values used by the existing
    App User/Auth implementation. ``FROZEN`` is intentionally additive.
    """

    ACTIVE = 0
    DISABLED = 1
    FROZEN = 2


class AppUserKycStatus(StrEnum):
    """Aggregated KYC status exposed by user-facing summary APIs."""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


APP_USER_STATUS_LABELS: dict[AppUserStatus, str] = {
    AppUserStatus.ACTIVE: "正常",
    AppUserStatus.DISABLED: "禁用",
    AppUserStatus.FROZEN: "冻结",
}

APP_USER_KYC_STATUS_LABELS: dict[AppUserKycStatus, str] = {
    AppUserKycStatus.UNVERIFIED: "未实名",
    AppUserKycStatus.PENDING: "待审核",
    AppUserKycStatus.VERIFIED: "已实名",
    AppUserKycStatus.REJECTED: "已驳回",
}

KYC_STATUS_TO_SUMMARY: dict[int, AppUserKycStatus] = {
    0: AppUserKycStatus.PENDING,
    1: AppUserKycStatus.VERIFIED,
    2: AppUserKycStatus.REJECTED,
}


def aggregate_kyc_status(status: int | None) -> AppUserKycStatus:
    """Map the existing KYC record status to the four summary states."""

    if status is None:
        return AppUserKycStatus.UNVERIFIED
    return KYC_STATUS_TO_SUMMARY.get(int(status), AppUserKycStatus.UNVERIFIED)


__all__ = [
    "APP_USER_KYC_STATUS_LABELS",
    "APP_USER_STATUS_LABELS",
    "AppUserKycStatus",
    "AppUserStatus",
    "KYC_STATUS_TO_SUMMARY",
    "aggregate_kyc_status",
]
